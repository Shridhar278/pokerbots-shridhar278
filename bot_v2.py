import dis
from operator import ne
import re

from engine import BIG_BLIND
from pkbot.actions import ActionFold, ActionCall, ActionCheck, ActionRaise, ActionBid
from pkbot.states import GameInfo, PokerState # the only one that matters
from pkbot.base import BaseBot
from pkbot.runner import parse_args, run_bot

import numpy as np
# Work on reducing computation time after A SUCCESSFULL RUN
from math import comb
BIG_BLIND = 20

class Player(BaseBot):

    def __init__(self) -> None:
        self.type = ['one_Pair', 'two_pair', 'three_of_a_kind', 'straight',
                     'flush', 'full_house', 'four_of_a_kind', 'straight_flush']
        # -1,0,1,2,3,4 FOLD - CALL - AGGRESSIVE - VERY AGGRESSIVE - MEGA AGGRESIVE - ALL_IN
        self.aggression=None 
        self.round=None
        self.cards=None
        self.states=None

    # odds for each type
    def alike_odds(self, role, want, sets, slots):
        total, need = sum(1 for v in self.states.values() if v is None), 0
        scope = [] #rank, free, count
        honor = None
        if (role==-1):
            total-=1
        else:
            total-=2
        for rank in 'AKQJT98765432':
            count=0
            free=0
            for suit in 'cdhs':
                if self.states[rank+suit] in (role, 0):
                    count+=1
                elif self.states[rank+suit] == None:
                    free+=1
            if count>=want:
                need+=1
                honor=rank
                if (need==sets):
                    return 1, honor
            else:
                count=want-count
                if count<=free:
                    scope.append([rank, free, count])
        if need==1:
            prob = [] # (rank1 (if necessary), rank2, probability
            for rank, free, count in scope:
                if (slots==1):
                    prob.append([rank, (comb(slots, count)*comb(free, count))/comb(total, slots)])
                else:
                    prob.append([min(rank, honor), max(rank, honor), (comb(slots, count)*comb(free, count))/comb(total, slots)])
            return prob
        else:
            prob = [] # (rank1, rank2, probability)
            for i in range(len(scope)-2):
                for j in range(i+1, len(scope)-1):
                    prob.append([scope[i][0], scope[j][0], (comb(slots, 2)*comb(scope[i][1], 1)*comb(scope[j][1], 1))/comb(total, slots)])
            return prob

    def high_card(self, role, slots):
        # not prob simple break tie metric
        for rank in 'AKQJT98765432':
            for suit in 'cdhs':
                if self.states[rank+suit] in (role, 0):
                    return rank

    def one_pair(self, role, slots):
        return self.alike_odds(role, 2, 1, slots)

    def two_pair(self, role, slots):
        return self.alike_odds(role, 2, 2, slots)
    
    def three_of_a_kind(self, role, slots):
        return self.alike_odds(role, 3, 1, slots)
    
    # def straight(self, role, slots):
    #     pass
    
    # def flush(self, role, slots):
    #     pass

    # def full_house(self, role, slots):
    #     return 

    def four_of_a_kind(self, role, slots):
        return self.alike_odds(role, 4, 1, slots)

    # def straight_flush(self, role, slots):
    #     pass

    def comparator_single(self, p1, p2, distro1, distro2):
        d1, d2 = 0, 0
        prob1, prob2 = 0, 0
        prob_a, prob_b= p1, p2
        rest = 1-(p1+p2)
        while d1<len(distro1) and d2<len(distro2):
            if (distro1[d1][0] < distro2[d2][0]):
                prob1=rest*distro1[d1][1]
                d1+=1
                if (d1==len(distro1)):
                    d1-=1
            elif (distro1[d1][0] > distro2[d2][0]):
                prob2=rest*distro2[d2][1]
                d2+=1
                if (d2==len(distro2)):
                    d2-=1
            else:
                prob1=rest*distro1[d1][1]*(1-distro2[d2][1])
                prob2=rest*distro2[d2][1]*(1-distro1[d1][1])
                d1+=1
                d2+=1
            prob_a += prob1
            prob_b += prob2
            rest = 1-(prob1+prob2)
        return prob_a, prob_b

    def compare_strength(self, slots):
        me, oppo= 0, 0
        # check for four of a kind:
        m_4 = self.four_of_a_kind(1, slots)
        o_4 = self.four_of_a_kind(-1, slots)
        me, oppo = self.comparator_single(me, oppo, m_4, o_4)
        # check for three of a kind:
        m_3 = self.three_of_a_kind(1, slots)
        o_3 = self.three_of_a_kind(-1, slots)
        me, oppo = self.comparator_single(me, oppo, m_3, o_3)
        # check for one pair:
        m_2x1 = self.one_pair(1, slots)
        o_2x1 = self.one_pair(-1, slots)
        me, oppo = self.comparator_single(me, oppo, m_2x1, o_2x1)
        # check for high card:
        my_high = self.high_card(1, slots)
        oppo_high = self.high_card(-1, slots)
        if (my_high >= oppo_high):
            me += 1-me-oppo
        else:
            oppo += 1-me-oppo
        return me, oppo

    def on_hand_start(self, game_info: GameInfo, current_state: PokerState) -> None:
        self.round = game_info.round_num
        self.cards = current_state.my_hand
        if self.cards[0][0]==self.cards[1][0]: # pair
            self.aggression=3
        elif self.cards[0][1]==self.cards[1][1]: # suited
            self.aggression=2
        elif self.cards[0][0] in 'AKQJ' or self.cards[1][0] in 'AKQJ': # high
            self.aggression=1
        else:
            self.aggression=0
        # -1 oppo 0 sharing 1 mine None not revealed
        self.states = {}
        for rank in '23456789TJQKA':
            for suit in 'cdhs':
                if (((rank in self.cards[0]) and (suit in self.cards[0])) or 
                    ((rank in self.cards[1]) and (suit in self.cards[1]))):
                    self.states[rank+suit] = 1
                else:
                    self.states[rank+suit] = None
        

    def on_hand_end(self, game_info: GameInfo, current_state: PokerState) -> None:
        pass

    def get_move(self, game_info: GameInfo, current_state: PokerState) -> ActionFold | ActionCall | ActionCheck | ActionRaise | ActionBid:
        street = current_state.street
        min_raise, max_raise = current_state.raise_bounds
        my_chips, oppo_chips = current_state.my_chips, current_state.opp_chips
        my_wager, oppo_wager = current_state.my_wager, current_state.opp_wager
        bet = [min_raise, min(min_raise*3, max_raise), min(min_raise*6, max_raise)]
        if current_state.opp_revealed_cards:
            for card in current_state.opp_revealed_cards:
                self.states[card] = -1
        if (current_state.board):
            for card in current_state.board:
                self.states[card] = 0
        if street == 'pre-flop':
            if (current_state.cost_to_call > BIG_BLIND*2 and self.aggression!=3):
                self.aggression=-1
                # our aggression starts post Auction
            if (self.aggression>0 and current_state.can_act(ActionRaise)):
                return ActionRaise(bet[self.aggression-1])
            elif (self.aggression==-1 and current_state.can_act(ActionFold)):
                return ActionFold()
            elif current_state.can_act(ActionCall):
                return ActionCall()
            elif current_state.can_act(ActionCheck):
                return ActionCheck()
        if street == 'auction':
            go_for_it = self.one_pair(1, 2)
            maximum = 0
            for rank, prob in go_for_it:
                maximum = max(maximum, prob)
            if maximum!=1:
                self.aggression=-1
                return ActionBid(0)
            else:
                return ActionBid(my_chips)
        after_flop = ['flop', 'turn', 'river']
        if street in after_flop:
            if (self.aggression==-1):
                if current_state.can_act(ActionFold):
                    return ActionFold()
                elif current_state.can_act(ActionCheck):
                    return ActionCheck()
                elif current_state.can_act(ActionRaise):
                    return ActionRaise(bet[0])
            my_win, oppo_win = self.compare_strength(2-after_flop.index(street))
            bet = [min_raise, min(min_raise*3, max_raise), min(min_raise*6, max_raise), max_raise]
            if my_win<0.5 and my_win>0.3:
                if current_state.can_act(ActionCall):
                    return ActionCall()
                elif current_state.can_act(ActionCheck):
                    return ActionCheck()
                elif current_state.can_act(ActionRaise):
                    return ActionRaise(bet[0])
            elif my_win<=0.3:
                if current_state.can_act(ActionCheck):
                    return ActionCheck()
                elif current_state.can_act(ActionFold):
                    return ActionFold()
                elif current_state.can_act(ActionRaise):
                    return ActionRaise(bet[0])
            if (current_state.can_act(ActionRaise)):
                if my_win>0.9:
                    return ActionRaise(bet[3])
                elif my_win>0.7:
                    return ActionRaise(bet[2])
                elif my_win>0.5:
                    return ActionRaise(bet[1])
            if (current_state.can_act(ActionCall)):
                return ActionCall()
            elif current_state.can_act(ActionCheck):
                return ActionCheck()


if __name__ == '__main__':
    run_bot(Player(), parse_args())