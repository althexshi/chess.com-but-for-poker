import io, itertools, random, time, os
from collections import Counter
from typing import List, Optional, Tuple
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

try: import joblib
except ImportError: joblib=None

st.set_page_config(page_title='Poker Arena',page_icon='♠️',layout='wide')
API=os.getenv('POKER_API_URL','http://localhost:8000')
WS=API.replace('http://','ws://').replace('https://','wss://')
RANKS='23456789TJQKA'; SUITS='♠♥♦♣'; RV={r:i+2 for i,r in enumerate(RANKS)}

def card_html(c:Optional[str], hidden=False):
    if hidden or c=='??': return '<div class="card back">♠</div>'
    if not c:return '<div class="card empty"></div>'
    cl='red' if c[1] in '♥♦' else 'black'; return f'<div class="card {cl}"><b>{c[0]}</b><span>{c[1]}</span></div>'

st.markdown('''<style>
.main-title{font-size:2.4rem;font-weight:850}.sub{color:#94a3b8}.table{background:radial-gradient(circle,#16834d,#075c38 72%);border:9px solid #5c3b22;border-radius:46%;padding:24px;min-height:390px}.cards,.board{display:flex;justify-content:center;gap:8px;min-height:92px}.board{margin:22px 0}.card{width:62px;height:88px;background:#fff;border-radius:9px;padding:7px;display:flex;flex-direction:column;justify-content:space-between;font-size:23px;box-shadow:0 6px 15px #0005}.red{color:#dc2626}.black{color:#111}.back{background:repeating-linear-gradient(45deg,#1e3a8a,#1e3a8a 8px,#2563eb 8px,#2563eb 16px);color:#fff;align-items:center;justify-content:center}.empty{background:#ffffff22;box-shadow:none}.name{text-align:center;color:white;font-weight:800}.pill{text-align:center;color:white}.status{padding:14px;border:1px solid #3b82f640;background:#3b82f615;border-radius:12px}.coach{padding:14px;border:1px solid #22c55e55;background:#22c55e12;border-radius:12px;margin-top:10px}
</style>''',unsafe_allow_html=True)
st.markdown('<div class="main-title">♠️ Poker Arena</div><div class="sub">Play against the computer or challenge another player live.</div>',unsafe_allow_html=True)

mode=st.sidebar.radio('Game mode',['🤖 Vs Computer','🌐 Multiplayer'])
coach_on=st.sidebar.toggle('Learning coach',value=True,help='Shows private feedback after each decision.')

# ---------- VS COMPUTER (compact engine based on your existing version) ----------
def init_bot():
    d={'pstack':100.0,'bstack':100.0,'pot':0.0,'deck':[],'ph':[],'bh':[],'board':[],'street':'Preflop','to_call':0.0,'over':True,'show':False,'msg':'Press New Hand','hands':0,'wins':0,'raises':0,'calls':0,'folds':0,'start':time.time(),'history':[],'model':None,'model_name':None,'feedback':None,'decision_scores':[]}
    for k,v in d.items():
        if 'bot_'+k not in st.session_state: st.session_state['bot_'+k]=v

def b(k): return st.session_state['bot_'+k]
def bs(k,v): st.session_state['bot_'+k]=v

def newdeck(): d=[r+s for r in RANKS for s in SUITS]; random.shuffle(d); return d

def strength(h,b):
    a,c=RV[h[0][0]],RV[h[1][0]]; s=(a+c)/28 + (0.3 if a==c else 0)+(0.07 if h[0][1]==h[1][1] else 0)
    return min(1,s + (0.12*len(b) if b else 0))

def coach_feedback(hole, board, pot, to_call, action, street):
    hand_strength = strength(hole, board)
    pot_odds = to_call / max(pot + to_call, 0.01) if to_call > 0 else 0.0
    if to_call > 0:
        fold = max(5, round((1-hand_strength)*70))
        call = max(10, round(45-abs(hand_strength-pot_odds)*35))
        raise_pct = max(5, 100-fold-call)
    else:
        fold = 0
        raise_pct = max(10, round(hand_strength*70))
        call = 100-raise_pct
    mix={'Fold':fold,'Check/Call':call,'Bet/Raise':raise_pct}
    normalized='Fold' if action=='fold' else ('Bet/Raise' if action=='bet' else 'Check/Call')
    best=max(mix,key=mix.get)
    freq=mix.get(normalized,0)
    score=100 if normalized==best else 70 if freq>=25 else 35 if freq>=10 else 0
    if hand_strength>=.70:
        why='Your estimated hand strength is high, so aggressive actions usually gain more value.'
    elif hand_strength>=.42:
        why='This is a medium-strength spot where multiple actions can be reasonable.'
    else:
        why='Your estimated hand strength is low, so pot control and folding to pressure matter more.'
    concept=(f'Calling requires roughly {pot_odds:.0%} equity from the pot odds.' if to_call>0 else 'Because no bet is facing you, checking controls the pot while betting applies pressure.')
    return {'street':street,'chosen_action':normalized,'score':score,'best_action':best,'mix':mix,'pot_odds':pot_odds,'estimated_strength':hand_strength,'explanation':why+' '+concept}

def show_learning(feedback, title='Decision Review'):
    if not feedback:
        st.info('Make a decision to receive coaching feedback.')
        return
    st.markdown(f'### {title}')
    st.markdown(
    f"""
    <div class="decision-review-grid">
        <div class="decision-review-card">
            <div class="decision-review-label">Decision score</div>
            <div class="decision-review-value">
                {feedback['score']}/100
            </div>
        </div>

        <div class="decision-review-card">
            <div class="decision-review-label">Suggested action</div>
            <div class="decision-review-value decision-action-value">
                {feedback['best_action']}
            </div>
        </div>

        <div class="decision-review-card">
            <div class="decision-review-label">Estimated strength</div>
            <div class="decision-review-value">
                {feedback['estimated_strength']:.0%}
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
    st.write(f"**You chose:** {feedback['chosen_action']}")
    for label,value in feedback['mix'].items():
        st.write(f'{label} — {value}%')
        st.progress(value/100)
    st.markdown(f"<div class='coach'><b>Why:</b> {feedback['explanation']}</div>",unsafe_allow_html=True)
    st.caption('These frequencies are educational heuristics, not exact solver-approved GTO outputs.')

def commit(who,amt):
    key='pstack' if who=='p' else 'bstack'; paid=min(amt,b(key)); bs(key,b(key)-paid); bs('pot',b('pot')+paid); return paid

def bot_new():
    d=newdeck(); bs('deck',d); bs('ph',[d.pop(),d.pop()]); bs('bh',[d.pop(),d.pop()]); bs('board',[]); bs('street','Preflop'); bs('pot',0.0); bs('over',False); bs('show',False); commit('b',.5); commit('p',1)
    if strength(b('bh'),[])>.62: commit('b',2); bs('to_call',1.5); bs('msg','Computer raises. Your turn.')
    else: commit('b',.5); bs('to_call',0); bs('msg','Computer calls. Check or raise.')

def bot_award(winner,text):
    key='pstack' if winner=='p' else 'bstack'; bs(key,b(key)+b('pot')); pot=b('pot'); bs('pot',0); bs('over',True); bs('hands',b('hands')+1); bs('show',True); bs('msg',text+f' Pot: {pot:.1f} BB'); bs('wins',b('wins')+(1 if winner=='p' else 0))

def advance():
    if b('street')=='Preflop': b('board').extend([b('deck').pop() for _ in range(3)]); bs('street','Flop')
    elif b('street')=='Flop': b('board').append(b('deck').pop()); bs('street','Turn')
    elif b('street')=='Turn': b('board').append(b('deck').pop()); bs('street','River')
    else:
        # simplified showdown strength
        if strength(b('ph'),b('board'))>=strength(b('bh'),b('board')): bot_award('p','You win at showdown.')
        else: bot_award('b','Computer wins at showdown.')
        return
    bs('to_call',0)
    if random.random() < strength(b('bh'),b('board'))*.55:
        bet=commit('b',max(1,round(b('pot')*.5,1))); bs('to_call',bet); bs('msg',f'{b("street")}: computer bets {bet:.1f} BB.')
    else: bs('msg',f'{b("street")}: computer checks. Your turn.')

def bot_action(action,f=.5):
    feedback=coach_feedback(b('ph'),b('board'),b('pot'),b('to_call'),action,b('street'))
    bs('feedback',feedback); bs('decision_scores',b('decision_scores')+[feedback['score']])
    if action=='fold': bs('folds',b('folds')+1); bot_award('b','You folded.'); return
    if action=='call':
        if b('to_call')>0: bs('calls',b('calls')+1); commit('p',b('to_call')); bs('to_call',0)
        advance(); return
    bs('raises',b('raises')+1); amt=commit('p',b('to_call')+max(1,round(b('pot')*f,1))); bs('to_call',0)
    if random.random()>strength(b('bh'),b('board'))+.12: bot_award('p','Computer folded.')
    else: commit('b',amt); advance()

def render_table(top_name,top_stack,top_cards,board,bottom_cards,bottom_name,bottom_stack,street,pot):
    st.markdown(f'''<div class="table"><div class="name">{top_name} · {top_stack:.1f} BB</div><div class="cards">{''.join(top_cards)}</div><div class="board">{''.join(board)}</div><div class="pill">{street} · Pot {pot:.1f} BB</div><div class="cards">{''.join(bottom_cards)}</div><div class="name">{bottom_name} · {bottom_stack:.1f} BB</div></div>''',unsafe_allow_html=True)

if mode.startswith('🤖'):
    init_bot()
    if st.sidebar.button('🎴 New Hand',type='primary',use_container_width=True,disabled=not b('over')): bot_new(); st.rerun()
    if st.sidebar.button('Reset computer match',use_container_width=True):
        for k in list(st.session_state):
            if k.startswith('bot_'): del st.session_state[k]
        st.rerun()
    m=st.columns(5); vals=[('You',f'{b("pstack"):.1f} BB'),('Computer',f'{b("bstack"):.1f} BB'),('Pot',f'{b("pot"):.1f} BB'),('Hands',b('hands')),('Wins',b('wins'))]
    for c,(x,y) in zip(m,vals): c.metric(x,y)
    l,r=st.columns([1.55,1]);
    with l:
        render_table('COMPUTER',b('bstack'),[card_html(c,not b('show')) for c in b('bh')] or [card_html(None),card_html(None)],[card_html(c) for c in b('board')]+[card_html(None)]*(5-len(b('board'))),[card_html(c) for c in b('ph')] or [card_html(None),card_html(None)],'YOU',b('pstack'),b('street'),b('pot'))
    with r:
        st.markdown(f'<div class="status"><b>{b("msg")}</b></div>',unsafe_allow_html=True)
        if not b('over'):
            c1,c2,c3=st.columns(3)
            if c1.button('Fold',use_container_width=True): bot_action('fold'); st.rerun()
            if c2.button(f'Call {b("to_call"):.1f}' if b('to_call') else 'Check',type='primary',use_container_width=True): bot_action('call'); st.rerun()
            if c3.button('½ Pot',use_container_width=True): bot_action('bet',.5); st.rerun()
            c4,c5=st.columns(2)
            if c4.button('¾ Pot',use_container_width=True): bot_action('bet',.75); st.rerun()
            if c5.button('Pot',use_container_width=True): bot_action('bet',1); st.rerun()
        else: st.info('Start a new hand.')
        if coach_on:
            show_learning(b('feedback'))

# ---------- MULTIPLAYER ----------
else:
    for k,v in {'room':'','token':'','name':'','connected':False}.items():
        if 'mp_'+k not in st.session_state: st.session_state['mp_'+k]=v
    st.sidebar.subheader('Multiplayer lobby')
    name=st.sidebar.text_input('Display name',value=st.session_state.mp_name or 'Player')
    tab1,tab2=st.sidebar.tabs(['Create','Join'])
    with tab1:
        if st.button('Create room',use_container_width=True):
            try:
                x=requests.post(API+'/create',json={'player_name':name},timeout=5).json(); st.session_state.mp_room=x['room_code']; st.session_state.mp_token=x['player_token']; st.session_state.mp_name=name; st.session_state.mp_connected=True; st.rerun()
            except Exception as e: st.error(f'Backend unavailable: {e}')
    with tab2:
        code=st.text_input('Room code').upper()
        if st.button('Join room',use_container_width=True):
            try:
                res=requests.post(API+'/join',json={'room_code':code,'player_name':name},timeout=5); res.raise_for_status(); x=res.json(); st.session_state.mp_room=x['room_code']; st.session_state.mp_token=x['player_token']; st.session_state.mp_name=name; st.session_state.mp_connected=True; st.rerun()
            except Exception as e: st.error(f'Could not join: {e}')
    if not st.session_state.mp_connected:
        st.info('Create a room or join with a room code. The FastAPI backend must be running.')
    else:
        room=st.session_state.mp_room; token=st.session_state.mp_token
        st.sidebar.success(f'Room: {room}')
        # Browser WebSocket: reload only when server pushes a state change.
        components.html(f'''<script>
        const key='poker_ws_last_{room}';
        const ws=new WebSocket('{WS}/ws/{room}');
        ws.onopen=()=>ws.send('ready');
        ws.onmessage=(e)=>{{const now=Date.now().toString(); if(sessionStorage.getItem(key)!==now){{sessionStorage.setItem(key,now); window.parent.location.reload();}}}};
        setInterval(()=>{{if(ws.readyState===1) ws.send('ping')}},20000);
        </script>''',height=0)
        try:
            state=requests.get(f'{API}/state/{room}/{token}',timeout=5).json()
        except Exception as e:
            st.error(f'Cannot read room: {e}'); st.stop()
        players=state['players']; you=players[0]; opp=players[1] if len(players)>1 else {'name':'Waiting…','stack':100,'hole':[],'wins':0}
        m=st.columns(5); vals=[('You',f"{you['stack']:.1f} BB"),('Opponent',f"{opp['stack']:.1f} BB"),('Pot',f"{state['pot']:.1f} BB"),('Your wins',you.get('wins',0)),('Room',room)]
        for c,(x,y) in zip(m,vals): c.metric(x,y)
        l,r=st.columns([1.55,1])
        with l:
            render_table(opp['name'],opp['stack'],[card_html(c) for c in opp.get('hole',[])] or [card_html(None),card_html(None)],[card_html(c) for c in state.get('board',[])]+[card_html(None)]*(5-len(state.get('board',[]))),[card_html(c) for c in you.get('hole',[])] or [card_html(None),card_html(None)],you['name'],you['stack'],state['street'],state['pot'])
        with r:
            st.markdown(f'<div class="status"><b>{state["message"]}</b></div>',unsafe_allow_html=True)
            def send(action,amount=0):
                res=requests.post(API+'/action',json={'room_code':room,'player_token':token,'action':action,'amount':amount},timeout=5)
                if not res.ok: st.error(res.text)
                else: st.rerun()
            if len(players)<2: st.warning('Waiting for Player 2 to join.')
            elif state['hand_over']:
                if st.button('🎴 Start New Hand',type='primary',use_container_width=True):
                    requests.post(API+'/new-hand',json={'room_code':room,'player_token':token,'action':'new'},timeout=5); st.rerun()
            elif state['turn_is_yours']:
                tc=state.get('to_call',0); c1,c2,c3=st.columns(3)
                if c1.button('Fold',use_container_width=True): send('fold')
                if c2.button(f'Call {tc:.1f}' if tc else 'Check',type='primary',use_container_width=True): send('call' if tc else 'check')
                if c3.button('½ Pot',use_container_width=True): send('bet',max(1,state['pot']*.5))
                c4,c5=st.columns(2)
                if c4.button('¾ Pot',use_container_width=True): send('bet',max(1,state['pot']*.75))
                if c5.button('Pot',use_container_width=True): send('bet',max(1,state['pot']))
            else: st.info(f"Waiting for {opp['name']}… This page updates automatically through WebSockets.")
            if coach_on:
                show_learning(state.get('learning_feedback'),title='Your Private Decision Review')


st.divider()
with st.expander('📚 Learning Center: core poker concepts'):
    t1,t2,t3,t4=st.tabs(['Pot odds','Position','Bet sizing','GTO-style thinking'])
    with t1:
        st.write('Pot odds compare the amount you must call with the total pot after calling. A call generally needs enough equity to justify that price.')
        st.code('required equity = amount to call / (current pot + amount to call)')
    with t2:
        st.write('Acting later gives you more information. In heads-up poker, the dealer acts first preflop but last on later streets.')
    with t3:
        st.write('Smaller bets risk fewer chips and can be used frequently. Larger bets apply more pressure but usually need stronger hands or carefully selected bluffs.')
    with t4:
        st.write('A GTO-style strategy can mix actions instead of always choosing one move. The percentages in this prototype demonstrate that idea, but they are simplified heuristics until your trained strategy model is connected.')
