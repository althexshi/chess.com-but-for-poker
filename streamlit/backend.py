import json, random, sqlite3, string, itertools
from collections import Counter
from contextlib import closing
from typing import Dict, List, Tuple

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

DB = 'poker_rooms.db'
app = FastAPI(title='Poker Multiplayer Backend')
RANKS='23456789TJQKA'; SUITS='♠♥♦♣'; RV={r:i+2 for i,r in enumerate(RANKS)}

class CreateBody(BaseModel):
    player_name: str
class JoinBody(BaseModel):
    room_code: str
    player_name: str
class ActionBody(BaseModel):
    room_code: str
    player_token: str
    action: str
    amount: float = 0

class Manager:
    def __init__(self): self.rooms: Dict[str, List[WebSocket]] = {}
    async def connect(self, room, ws):
        await ws.accept(); self.rooms.setdefault(room, []).append(ws)
    def disconnect(self, room, ws):
        if room in self.rooms and ws in self.rooms[room]: self.rooms[room].remove(ws)
    async def broadcast(self, room, payload):
        dead=[]
        for ws in self.rooms.get(room, []):
            try: await ws.send_json(payload)
            except Exception: dead.append(ws)
        for ws in dead: self.disconnect(room, ws)
manager=Manager()

def db():
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
    con.execute('CREATE TABLE IF NOT EXISTS rooms(code TEXT PRIMARY KEY, state TEXT NOT NULL)')
    return con

def save(code, state):
    with closing(db()) as con:
        con.execute('INSERT OR REPLACE INTO rooms(code,state) VALUES(?,?)',(code,json.dumps(state))); con.commit()

def load(code):
    with closing(db()) as con:
        row=con.execute('SELECT state FROM rooms WHERE code=?',(code,)).fetchone()
    if not row: raise HTTPException(404,'Room not found')
    return json.loads(row['state'])

def deck():
    d=[r+s for r in RANKS for s in SUITS]; random.shuffle(d); return d

def eval5(cards):
    vals=sorted((RV[c[0]] for c in cards),reverse=True); suits=[c[1] for c in cards]; cnt=Counter(vals)
    groups=sorted(((n,v) for v,n in cnt.items()),reverse=True); flush=len(set(suits))==1
    uniq=sorted(set(vals),reverse=True); uniq += [1] if 14 in uniq else []
    sh=0
    for i in range(len(uniq)-4):
        if uniq[i]-uniq[i+4]==4: sh=uniq[i]; break
    if flush and sh:return (8,(sh,))
    if groups[0][0]==4:
        q=groups[0][1]; return (7,(q,max(v for v in vals if v!=q)))
    if groups[0][0]==3 and len(groups)>1 and groups[1][0]>=2:return (6,(groups[0][1],groups[1][1]))
    if flush:return (5,tuple(vals))
    if sh:return (4,(sh,))
    if groups[0][0]==3:
        t=groups[0][1]; return (3,(t,*sorted((v for v in vals if v!=t),reverse=True)[:2]))
    pairs=sorted((v for n,v in groups if n==2),reverse=True)
    if len(pairs)>=2:return (2,(pairs[0],pairs[1],max(v for v in vals if v not in pairs[:2])))
    if len(pairs)==1:
        p=pairs[0]; return (1,(p,*sorted((v for v in vals if v!=p),reverse=True)[:3]))
    return (0,tuple(vals))

def best(cards): return max(eval5(list(c)) for c in itertools.combinations(cards,5))



def estimate_strength(hole, board):
    if len(hole) < 2:
        return 0.0
    a, b = RV[hole[0][0]], RV[hole[1][0]]
    suited = hole[0][1] == hole[1][1]
    pair = a == b
    if not board:
        score = (a + b) / 28
        if pair:
            score += 0.24 + a / 65
        if suited:
            score += 0.07
        if abs(a - b) <= 2:
            score += 0.04
        return min(score, 1.0)
    rank = best(hole + board)
    category, kickers = rank
    return min(1.0, category / 8 + (kickers[0] / 100 if kickers else 0))

def learning_feedback(state, idx, chosen_action):
    opp = 1 - idx
    mine = state['street_bets'][idx]
    theirs = state['street_bets'][opp]
    call = max(0.0, theirs - mine)
    pot_before = max(state['pot'], 0.01)
    pot_odds = call / (pot_before + call) if call > 0 else 0.0
    strength = estimate_strength(state['players'][idx]['hole'], state['board'])

    if call > 0:
        fold = max(5, round((1 - strength) * 70))
        call_pct = max(10, round(45 - abs(strength - pot_odds) * 35))
        raise_pct = max(5, 100 - fold - call_pct)
    else:
        fold = 0
        raise_pct = max(10, round(strength * 70))
        call_pct = 100 - raise_pct

    mix = {'Fold': fold, 'Check/Call': call_pct, 'Bet/Raise': raise_pct}
    best_action = max(mix, key=mix.get)
    normalized = 'Fold' if chosen_action == 'fold' else ('Bet/Raise' if chosen_action == 'bet' else 'Check/Call')
    chosen_frequency = mix.get(normalized, 0)
    score = 100 if normalized == best_action else 70 if chosen_frequency >= 25 else 35 if chosen_frequency >= 10 else 0

    if call > 0:
        concept = f'You needed about {pot_odds:.0%} equity to call based on pot odds.'
    else:
        concept = 'No bet was facing you, so checking preserves the pot while betting applies pressure.'
    if strength >= 0.7:
        reason = 'Your estimated hand strength is high, so aggressive actions gain more value.'
    elif strength >= 0.42:
        reason = 'This is a medium-strength spot where more than one action can be reasonable.'
    else:
        reason = 'Your estimated hand strength is low, so pot control and folding to pressure become more important.'
    return {
        'street': state['street'],
        'chosen_action': normalized,
        'score': score,
        'best_action': best_action,
        'mix': mix,
        'pot_odds': round(pot_odds, 4),
        'estimated_strength': round(strength, 4),
        'explanation': reason + ' ' + concept,
    }

def public(state, token):
    idx=0 if state['players'][0]['token']==token else 1 if len(state['players'])>1 and state['players'][1]['token']==token else -1
    if idx<0: raise HTTPException(403,'Invalid player token')
    opp=1-idx
    reveal=state['hand_over'] and state.get('showdown',False)
    feedback = state.get('feedback', {}).get(token)
    return {**state,'deck':None,'learning_feedback':feedback,'players':[
        {k:v for k,v in state['players'][idx].items() if k!='token'},
        {**{k:v for k,v in state['players'][opp].items() if k not in ('token','hole')},'hole':state['players'][opp]['hole'] if reveal else ['??','??']}
    ],'you_index':0,'turn_is_yours':state['turn']==idx and not state['hand_over']}

def new_hand(state):
    if len(state['players'])<2: raise HTTPException(400,'Waiting for second player')
    d=deck(); state.update({'deck':d,'board':[],'street':'Preflop','pot':0.0,'to_call':0.5,'hand_over':False,'showdown':False,'message':'New hand started','acted':[False,False],'feedback':{}})
    for p in state['players']: p['hole']=[state['deck'].pop(),state['deck'].pop()]
    dealer=state.get('dealer',0); state['dealer']=1-dealer; sb=state['dealer']; bb=1-sb
    state['players'][sb]['stack']-=0.5; state['players'][bb]['stack']-=1.0; state['pot']=1.5
    state['street_bets']=[0.5 if i==sb else 1.0 for i in range(2)]; state['turn']=sb
    state['message']=f"{state['players'][sb]['name']} acts first preflop"

def next_street(state):
    if state['street']=='Preflop': state['board'] += [state['deck'].pop() for _ in range(3)]; state['street']='Flop'
    elif state['street']=='Flop': state['board'].append(state['deck'].pop()); state['street']='Turn'
    elif state['street']=='Turn': state['board'].append(state['deck'].pop()); state['street']='River'
    else: return showdown(state)
    state['street_bets']=[0,0]; state['to_call']=0; state['acted']=[False,False]; state['turn']=1-state['dealer']; state['message']=f"{state['street']}"

def showdown(state):
    while len(state['board'])<5: state['board'].append(state['deck'].pop())
    a,b=best(state['players'][0]['hole']+state['board']),best(state['players'][1]['hole']+state['board'])
    state['showdown']=True; state['hand_over']=True
    if a>b: w=0
    elif b>a: w=1
    else:
        state['players'][0]['stack']+=state['pot']/2; state['players'][1]['stack']+=state['pot']/2; state['message']='Tie — pot split'; state['pot']=0; return
    state['players'][w]['stack']+=state['pot']; state['players'][w]['wins']+=1; state['message']=f"{state['players'][w]['name']} wins at showdown"; state['pot']=0

def apply_action(state, idx, action, amount):
    if state['hand_over'] or state['turn']!=idx: raise HTTPException(400,'Not your turn')
    opp=1-idx; mine=state['street_bets'][idx]; theirs=state['street_bets'][opp]; call=max(0,theirs-mine)
    p=state['players'][idx]
    token=p['token']
    state.setdefault('feedback', {})[token]=learning_feedback(state, idx, action)
    if action=='fold':
        state['players'][opp]['stack']+=state['pot']; state['players'][opp]['wins']+=1; state['pot']=0; state['hand_over']=True; state['message']=f"{p['name']} folded"
        return
    if action in ('check','call'):
        pay=min(call,p['stack']); p['stack']-=pay; state['pot']+=pay; state['street_bets'][idx]+=pay; state['acted'][idx]=True
    elif action=='bet':
        target=max(theirs, mine+max(1.0,amount)); pay=min(target-mine,p['stack']); p['stack']-=pay; state['pot']+=pay; state['street_bets'][idx]+=pay; state['acted']=[False,False]; state['acted'][idx]=True
    else: raise HTTPException(400,'Unknown action')
    if p['stack']==0 or state['players'][opp]['stack']==0: showdown(state); return
    equal=abs(state['street_bets'][0]-state['street_bets'][1])<1e-9
    if equal and all(state['acted']): next_street(state)
    else: state['turn']=opp; state['to_call']=max(0,state['street_bets'][idx]-state['street_bets'][opp]); state['message']=f"{state['players'][opp]['name']}'s turn"

@app.post('/create')
async def create(body:CreateBody):
    code=''.join(random.choices(string.ascii_uppercase+string.digits,k=6)); token=''.join(random.choices(string.ascii_letters+string.digits,k=24))
    state={'code':code,'players':[{'name':body.player_name,'token':token,'stack':100.0,'hole':[],'wins':0}], 'board':[],'street':'Waiting','pot':0,'turn':-1,'to_call':0,'hand_over':True,'showdown':False,'message':'Waiting for Player 2','dealer':1,'history':[],'feedback':{}}
    save(code,state); return {'room_code':code,'player_token':token}

@app.post('/join')
async def join(body:JoinBody):
    state=load(body.room_code.upper())
    if len(state['players'])>=2: raise HTTPException(400,'Room full')
    token=''.join(random.choices(string.ascii_letters+string.digits,k=24)); state['players'].append({'name':body.player_name,'token':token,'stack':100.0,'hole':[],'wins':0}); save(state['code'],state)
    await manager.broadcast(state['code'],{'type':'room_update'}); return {'room_code':state['code'],'player_token':token}

@app.get('/state/{code}/{token}')
async def state(code:str,token:str): return public(load(code.upper()),token)

@app.post('/new-hand')
async def start(body:ActionBody):
    state=load(body.room_code.upper()); idx=next((i for i,p in enumerate(state['players']) if p['token']==body.player_token),-1)
    if idx<0: raise HTTPException(403,'Invalid token')
    new_hand(state); save(state['code'],state); await manager.broadcast(state['code'],{'type':'state_changed'}); return {'ok':True}

@app.post('/action')
async def action(body:ActionBody):
    state=load(body.room_code.upper()); idx=next((i for i,p in enumerate(state['players']) if p['token']==body.player_token),-1)
    if idx<0: raise HTTPException(403,'Invalid token')
    apply_action(state,idx,body.action,body.amount); save(state['code'],state); await manager.broadcast(state['code'],{'type':'state_changed'}); return {'ok':True}

@app.websocket('/ws/{code}')
async def ws(code:str, websocket:WebSocket):
    code=code.upper(); await manager.connect(code,websocket)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: manager.disconnect(code,websocket)
