import random
import requests


url = "WEBHOOK API" #HL

card_list=dict()
suits=["♣", "♦", "♥", "♠"]
number=["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K" , "A"][::-1]
#print(number)
players=4#int(input("Players: "))
cards=[[]for _ in range(players)]
poker=[i+j for i in suits for j in number]
o=0
u=","
rest=[]
for m in range(52%players):
    tmp=poker.pop(random.randint(0,len(poker)-1))
    rest.append(tmp)
while len(poker)>0:
    x=random.randint(0,players-1)
    if len(cards[x])!=52//players:
#        cards[x].append(poker[o])
#        poker.remove(poker[o])
        cards[x].append(poker.pop(o))
for h in range(0,players):
    card_list[f"Player{h+1}"]=cards[h]
#print(card_list)

for k,v in card_list.items():
    tmp=[[],[],[],[]]
    nows=0
    for e in v:
        while e[0]!=suits[nows]:
            #print(nows)
            nows+=1
            if nows==players:break
        tmp[nows].append(e[1:])
    card_list[k]=tmp
#print(card_list)
#print("rest: ",end="")
#print(",".join(rest))
#card_list[f"rest"]=rest
#print(card_list)
find={"Player1":"N","Player2":"E","Player3":"S","Player4":"W"}
response=requests.post(url,data={"content":"--------------------"})
for k,v in card_list.items():
    hcp=0
    for l in v:
        for e in l:
            if e=='A':hcp+=4
            if e=='K':hcp+=3
            if e=='Q':hcp+=2
            if e=='J':hcp+=1
    payload={
            "content":f'{k}({find[k]}): HCP=||{hcp}\nC: {" ".join(v[0])if len(v[0])else None}\nD: {' '.join(v[1])if len(v[1])else None}\nH: {' '.join(v[2])if len(v[2])else None}\nS: {' '.join(v[3])if len(v[3])else None}||'
    }
    print(payload["content"])
    response = requests.post(url,data=payload)
response=requests.post(url,data={"content":f"Dealer: {find["Player"+str(random.randint(1,4))]}"})
