'''
First Attempt at Understanding the Game and Implementing a Bot
'''

from argparse import Action

from pkbot.actions import ActionFold, ActionCall, ActionCheck, ActionRaise, ActionBid
from pkbot.states import GameInfo, PokerState # the only one that matters
from pkbot.base import BaseBot
from pkbot.runner import parse_args, run_bot

import random
import numpy as np

class Player(BaseBot):

    def __init__(self) -> None:
        '''
        
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        '''
        # Pretty excited about this AGAIN
        pass

    def on_hand_start(self, game_info: GameInfo, current_state: PokerState) -> None:
        '''
        Called when a new round starts. Called NUM_ROUNDS times.

        Arguments:
        game_info: the GameInfo object.
        current_state: the PokerState object.

        Returns:
        Nothing.
        '''
        my_bankroll = game_info.bankroll  # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        # the total number of seconds your bot has left to play this game
        time_bank = game_info.time_bank
        round_num = game_info.round_num  # the round number from 1 to NUM_ROUNDS
        
        # your cards
        # is an array; eg: ['Ah', 'Kd'] for Ace of hearts and King of diamonds
        my_cards = current_state.my_hand

        # opponent's  revealed cards or [] if not revealed
        opp_revealed_cards = current_state.opp_revealed_cards
        
        big_blind = current_state.is_bb  # True if you are the big blind
        pass

    def on_hand_end(self, game_info: GameInfo, current_state: PokerState) -> None:
        '''
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_info: the GameInfo object.
        current_state: the PokerState object.

        Returns:
        Nothing.
        '''
        my_delta = current_state.payoff  # your bankroll change from this round
        
        street = current_state.street  # 'pre-flop', 'flop', 'auction', 'turn', or 'river'
        # your cards
        # is an array; eg: ['Ah', 'Kd'] for Ace of hearts and King of diamonds
        my_cards = current_state.my_hand

        # opponent's revealed cards or [] if not revealed
        opp_revealed_cards = current_state.opp_revealed_cards

    def get_move(self, game_info: GameInfo, current_state: PokerState) -> ActionFold | ActionCall | ActionCheck | ActionRaise | ActionBid:
        '''
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Arguments:
        game_info: the GameInfo object.
        current_state: the PokerState object.

        Returns:
        Your action.
        '''
        def check_power(hand):
        #     # , total, scope, role, pool

        #     # check for one pair, two pair, three of a kind, four of a kind, full house
        #     # and hopes for better
            alikes = [0 for _ in range(13)]
            suits = [0 for _ in range(4)]
            for card in hand+current_state.board:
                alikes['23456789TJQKA'.index(card[0])]+=1
                suits['cdhs'.index(card[1])]+=1
            best=0
            for card in hand+current_state.board:
                best=max('23456789TJQKA'.index(card[0]), best)
            # check for powers
            power=best # high card
            if max(alikes)==2 and alikes.count(2)==1: # one pair
                power=10000+100*alikes.index(2)
            elif max(alikes)==2 and alikes.count(2)==2: # two pair
                power=20000+alikes.index(2)+100*alikes.index(2, alikes.index(2)+1)
            elif max(alikes)==3: # three of a kind
                power=100000+100*alikes.index(3)
                if (2 in alikes): # full house
                    power=200000+100*alikes.index(3)+alikes.index(2)
            elif max(alikes)==4: # four of a kind
                power=3000000+100*alikes.index(4)

            # not taking these seriously
            if max(suits)>=5: # flush
                power=max(power, 150000)
                for i in range(8): # Straight-Flush
                    if alikes[i] and alikes[i+1] and alikes[i+2] and alikes[i+3] and alikes[i+4]:
                        power=max(power, 6000000+100*i)
                if alikes[8] and alikes[9] and alikes[10] and alikes[11] and alikes[12]: # Royal-Flush
                    power=max(power, 6000000+100*8)
                if alikes[0] and alikes[1] and alikes[2] and alikes[3] and alikes[12]: # Straight-Flush with Ace low
                    power=max(power, 9999999)
            for i in range(9): # Straight
                if alikes[i] and alikes[i+1] and alikes[i+2] and alikes[i+3] and alikes[i+4]:
                    power=max(power, 110000+100*i)
            if alikes[0] and alikes[1] and alikes[2] and alikes[3] and alikes[12]:
                power=max(power, 110000+100*0)
            
        #     # hopes
            hope=0
        #     # if scope==0:
        #     #     return power, hope
        #     # if scope==1:
        #     #     for s, suit in enumerate(total):
        #     #         for r, rank in enumerate(suit):
        #     #             if rank==role:
        #     #                 curr, times=0, 0
        #     #                 for i in range(4):
        #     #                     if (total[i][r]==0):
        #     #                         curr+=1
        #     #                     elif (total[i][r]==role):
        #     #                         times+=1
        #     #                 curr/=pool
        #     #                 if times==2 and power<200000:
        #     #                     hope=max(hope, (10000+100*r)*curr)
        #     #                 elif times==3 and power<100000:
        #     #                     hope=max(hope, (100000+100*r)*curr)
        #     #                 elif times==4 and power<3000000:
        #     #                     hope=max(hope, (3000000+100*r)*curr)

        #     # if scope==2:
        #     #     return power, hope
        #     # if scope==3:
        #     #     return power, hope
            return power, hope


        # Now, include Auction-searched data 
        # + ignoring just board accumulated hand stength
        # + little bit odds into the picture & potential
        # BLUFF just a little random.random()<0.1
        c1, c2 = current_state.my_hand
        min_raise, max_raise = current_state.raise_bounds
        good_raise = int(min(min_raise*5, max_raise))
        if current_state.street == 'pre-flop':
            if c1[0] == c2[0]:
                if (c1[0] in 'AKQJT'):
                    return ActionRaise(good_raise)
                return ActionRaise(min_raise)
            return ActionCall()
        if current_state.street == 'auction':
            bid = random.uniform(0.81, 0.99) * current_state.my_chips
            return ActionBid(int(bid))
        # all_cards =[[0 for _ in range(13)] for _ in range(4)]
        # count = 0
        # for card in current_state.board:
        #     all_cards['cdhs'.index(card[1])]['23456789TJQKA'.index(card[0])]=2
        #     count+=1
        # for card in current_state.my_hand:
        #     all_cards['cdhs'.index(card[1])]['23456789TJQKA'.index(card[0])]=1
        #     count+=1
        # oppo_power, oppo_hope=0 # considering always win auction
        if current_state.opp_revealed_cards:
            oppo = current_state.opp_revealed_cards
            # for card in oppo:
            #     all_cards['cdhs'.index(card[1])]['23456789TJQKA'.index(card[0])]=-1
            #     count+=1
            # oppo_power, oppo_hope = check_power(oppo, all_cards, 9-count, -1, 52-count)
            oppo_power, oppo_hope = check_power(oppo)
            # my_power, my_hope=check_power(current_state.my_hand, all_cards, 8-count, 1, 52-count)
            my_power, my_hope = check_power(current_state.my_hand)
        else:
            # my_power, my_hope=check_power(current_state.my_hand, all_cards, 7-count, 1, 52-count)
            my_power, my_hope = check_power(current_state.my_hand)
        if current_state.street in ['flop', 'turn', 'river']:
            my_power += my_hope
            oppo_power += oppo_hope
            if (current_state.can_act(ActionRaise)):
                if my_power>oppo_power:
                    if (my_power>10*oppo_power):
                        return ActionRaise(max_raise)
                    elif (my_power>2*oppo_power):
                        return ActionRaise(good_raise)
                    else:
                        return ActionRaise(min_raise)
            if current_state.can_act(ActionCheck):
                return ActionCheck()
            if my_power<oppo_power/5:
                if random.random()<0.95 and current_state.can_act(ActionCall):
                    return ActionCall()
                elif current_state.can_act(ActionFold):
                    return ActionFold()
                else:
                    return ActionRaise(min_raise)
            else:
                if current_state.can_act(ActionCall):
                    return ActionCall()
                else:
                    return ActionRaise(min_raise)


if __name__ == '__main__':
    run_bot(Player(), parse_args())