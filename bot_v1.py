'''
First Attempt at Understanding the Game and Implementing a Bot
'''
from pkbot.actions import ActionFold, ActionCall, ActionCheck, ActionRaise, ActionBid
from pkbot.states import GameInfo, PokerState # the only one that matters
from pkbot.base import BaseBot
from pkbot.runner import parse_args, run_bot

import random

class Player(BaseBot):

    def __init__(self) -> None:
        '''
        
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        '''
        # Pretty excited about this.
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

        # indegenious approach
        c1, c2 = current_state.my_hand
        min_raise, max_raise = current_state.raise_bounds
        solid_raise = int(max(min(max_raise/10, min_raise*10), min_raise))
        # the actions
        if current_state.street == 'auction':
            bid = random.uniform(0.6, 0.9) * current_state.my_chips
            return ActionBid(int(bid))
        if current_state.street == 'pre-flop':
            if (c1[0] == c2[0]) or (c1[0] in 'TAKQJ') or (c2[0] in 'TAKQJ'):  # good hand
                return ActionRaise(solid_raise)
            elif c1[1] == c2[1]: # suited
                return ActionRaise(min_raise)
            else:
                return ActionCall()
        if current_state.street in ['flop', 'turn', 'river']:
            # 0.full house, straight flush, royal flush -> LEAVE for NOW
            # 1.straight, flush, four of a kind -> max raise
            # 2.three of a kind -> solid raise
            # 3.two pair -> min raise
            # 4.one pair -> solid raise (bluff)
            # 5.nothing -> call if (random < 0.75) else fold
            alikes = [0 for _ in range(13)]
            suits = [0 for _ in range(4)]
            for card in current_state.my_hand + current_state.board:
                alikes['23456789TJQKA'.index(card[0])] += 1
                suits['cdhs'.index(card[1])] += 1
            
            if current_state.can_act(ActionRaise):
                if max(suits) >= 5: # Flush
                    return ActionRaise(max_raise)
                for i in range(9): # Straight
                    if alikes[i] and alikes[i+1] and alikes[i+2] and alikes[i+3] and alikes[i+4]:
                        return ActionRaise(max_raise)
                if alikes[12] and alikes[0] and alikes[1] and alikes[2] and alikes[3]:
                    return ActionRaise(max_raise)
                if max(alikes) >= 4: # Four of a Kind
                    return ActionRaise(max_raise)
            
                if max(alikes) >= 3: # Three Pair or better
                    return ActionRaise(solid_raise)
                elif max(alikes) == 2 and alikes.count(2) >= 2: # Two Pair
                    return ActionRaise(min_raise)
                elif max(alikes) == 2: # One Pair
                    return ActionRaise(solid_raise)
            
            if current_state.can_act(ActionCheck):
                return ActionCheck()
            
            if (random.random() < 0.75) and (current_state.can_act(ActionCall)):
                return ActionCall()
            elif current_state.can_act(ActionFold):
                return ActionFold()


if __name__ == '__main__':
    run_bot(Player(), parse_args())