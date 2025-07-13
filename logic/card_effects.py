# file: logic/card_effects.py
"""
This module contains the effect logic for each card.
Each function handles the complete effect of a card being played,
including player interaction, state changes, and UI updates via callbacks.

Each effect function has the signature:
def effect_function(game_round, acting_player, played_card, **kwargs)

- game_round: The main GameRound instance, providing access to game state and UI callbacks.
- acting_player: The player who played the card.
- played_card: The card object that was played.
- **kwargs: For effects that need data from a previous step (e.g., a selected target).

The function should return True if it requires further user input (and has shown a popup),
or False if the effect is resolved and the game can proceed to the next turn.
"""
import random
from .constants import CARD_PROTOTYPES

# --- Helper Functions ---

def _prepare_animation_data(acting_player, target_player, card, outcome, details):
    """A consistent way to create the data dictionary for the effect animation panel."""
    return {
        'acting_player': acting_player,
        'target_player': target_player,
        'card': card,
        'outcome': outcome,
        'details': details
    }


def _get_generic_targets(game_round, acting_player, include_self=False, unprotected_only=True, allow_no_hand=False):
    """A generic target-finding utility used by many card effects."""
    return game_round.get_valid_targets(
        acting_player,
        include_self=include_self,
        targeted_effect_requires_unprotected=unprotected_only,
        allow_no_hand=allow_no_hand
    )

# --- Guard Effect ---

def effect_guard(game_round, acting_player, card_played, **kwargs):
    valid_targets = _get_generic_targets(game_round, acting_player)
    if acting_player.sycophant_target_self:
        game_round.log_message(f"Kẻ nịnh bợ: {acting_player.name} phải tự chọn mình, nhưng Cận vệ không thể. Hiệu ứng mất.")
        return False
    if not valid_targets:
        game_round.log_message("Cận vệ: Không có mục tiêu hợp lệ.")
        return False

    if 'target_player_id' in kwargs:
        return _resolve_guard_target_selected(game_round, acting_player, card_played, kwargs['target_player_id'])

    if acting_player.is_cpu:
        target_player = random.choice(valid_targets)
        possible_values = sorted(list(set(proto.value for name, proto in CARD_PROTOTYPES.items()
                                          if proto.value != 1 and game_round.is_card_in_current_deck(name))))
        if not possible_values:
            game_round.log_message("Cận vệ (Máy): Không có giá trị hợp lệ để đoán!")
            return False
        guess_val = random.choice(possible_values)
        game_round.log_message(f"Máy ({acting_player.name}) chơi Cận vệ lên {target_player.name}, đoán giá trị {guess_val}.")
        _resolve_guard_guess(game_round, acting_player, target_player, guess_val, game_round.finish_effect_and_proceed)
        return True
    else:
        game_round.ui['request_target_selection_callback'](
            acting_player, card_played, valid_targets,
            lambda ap, tid: effect_guard(game_round, ap, card_played, target_player_id=tid),
            game_round.cancel_played_card_action
        )
        return True

def _resolve_guard_target_selected(game_round, acting_player, card_played, target_player_id):
    target_player = next(p for p in game_round.players if p.id == target_player_id)
    possible_values = sorted(list(set(proto.value for name, proto in CARD_PROTOTYPES.items()
                                       if proto.value != 1 and game_round.is_card_in_current_deck(name))))
    if not possible_values:
        game_round.log_message(f"Cận vệ: Không có giá trị hợp lệ để đoán {target_player.name}! Hiệu ứng mất.")
        game_round.finish_effect_and_proceed()
        return True # Handled

    game_round.ui['request_guard_value_popup_callback'](
        acting_player, target_player, possible_values,
        lambda ap, tp, gv: _resolve_guard_guess(game_round, ap, tp, gv, game_round.finish_effect_and_proceed),
        game_round.cancel_played_card_action
    )
    return True # Handled

def _resolve_guard_guess(game_round, acting_player, target_player, guessed_value, continuation):
    game_round.log_message(f"{acting_player.name} (Cận vệ) đoán giá trị {guessed_value} cho {target_player.name}.")
    if not target_player.hand:
        game_round.log_message(f"Đoán vào {target_player.name}, nhưng họ không có bài.")
        if continuation: continuation()
        return

    target_card = target_player.hand[0]
    is_assassin = game_round.is_card_in_current_deck('Assassin') and target_card.name == 'Assassin'
    is_correct_guess = target_card.value == guessed_value
    outcome = 'reversed' if is_assassin else 'success' if is_correct_guess else 'fail'
    details = {'guessed_value': guessed_value, 'target_card': target_card}

    def final_logic():
        if outcome == 'reversed':
            game_round.log_message(f"{target_player.name} lộ ra Sát thủ! {acting_player.name} bị loại!")
            def assassin_continuation():
                if game_round.ui.get('add_to_global_discard_callback'):
                    game_round.ui['add_to_global_discard_callback'](target_player, target_card)
                target_player.play_card('Assassin')
                new_card = game_round.draw_from_deck_or_burned()
                if new_card: target_player.add_card_to_hand(new_card)
                game_round.log_message(f"{target_player.name} bỏ Sát thủ và rút một lá bài mới.")
                if continuation: continuation()
            game_round.eliminate_player(acting_player, assassin_continuation)
        elif outcome == 'success':
            game_round.log_message(f"Đoán đúng! {target_player.name} có {target_card.name}. Đã bị loại.")
            game_round.eliminate_player(target_player, continuation)
        else: # Fail
            game_round.log_message(f"Đoán sai. {target_player.name} không có lá bài giá trị {guessed_value}.")
            if continuation: continuation()

    animation_data = _prepare_animation_data(acting_player, target_player, CARD_PROTOTYPES['Guard'], outcome, details)
    game_round.ui['animate_card_effect_callback'](animation_data, final_logic)


# --- Priest Effect ---

def effect_priest(game_round, acting_player, card_played, **kwargs):
    valid_targets = _get_generic_targets(game_round, acting_player)
    if acting_player.sycophant_target_self:
        game_round.log_message(f"Kẻ nịnh bợ: {acting_player.name} phải tự chọn mình, nhưng Mục sư không thể. Hiệu ứng mất.")
        return False
    if not valid_targets:
        game_round.log_message("Mục sư: Không có mục tiêu hợp lệ.")
        return False

    if 'target_player_id' in kwargs:
        target_player = next(p for p in game_round.players if p.id == kwargs['target_player_id'])
        _resolve_priest_effect(game_round, acting_player, target_player, game_round.finish_effect_and_proceed)
        return True

    if acting_player.is_cpu:
        target_player = random.choice(valid_targets)
        _resolve_priest_effect(game_round, acting_player, target_player, game_round.finish_effect_and_proceed)
        return True
    else:
        game_round.ui['request_target_selection_callback'](
            acting_player, card_played, valid_targets,
            lambda ap, tid: effect_priest(game_round, ap, card_played, target_player_id=tid),
            game_round.cancel_played_card_action
        )
        return True

def _resolve_priest_effect(game_round, acting_player, target_player, continuation):
    if not target_player.hand:
        game_round.log_message(f"{target_player.name} không có bài để xem (Mục sư).")
        if continuation: continuation()
        return

    target_card = target_player.hand[0]
    details = {'target_card': target_card}
    def final_logic():
        log_msg = f"{acting_player.name} nhìn vào tay của {target_player.name}."
        if not acting_player.is_cpu:
            log_msg += f" Họ thấy lá {target_card.name}."
        game_round.log_message(log_msg)
        if continuation: continuation()

    animation_data = _prepare_animation_data(acting_player, target_player, card=CARD_PROTOTYPES['Priest'], outcome='neutral', details=details)
    game_round.ui['animate_card_effect_callback'](animation_data, final_logic)


# --- Baron Effect ---

def effect_baron(game_round, acting_player, card_played, **kwargs):
    valid_targets = _get_generic_targets(game_round, acting_player)
    if acting_player.sycophant_target_self:
        game_round.log_message(f"Kẻ nịnh bợ: {acting_player.name} phải tự chọn mình, nhưng Nam tước không thể. Hiệu ứng mất.")
        return False
    if not valid_targets:
        game_round.log_message("Nam tước: Không có mục tiêu hợp lệ.")
        return False

    if 'target_player_id' in kwargs:
        target_player = next(p for p in game_round.players if p.id == kwargs['target_player_id'])
        _resolve_baron_effect(game_round, acting_player, target_player, game_round.finish_effect_and_proceed)
        return True

    if acting_player.is_cpu:
        target_player = random.choice(valid_targets)
        _resolve_baron_effect(game_round, acting_player, target_player, game_round.finish_effect_and_proceed)
        return True
    else:
        game_round.ui['request_target_selection_callback'](
            acting_player, card_played, valid_targets,
            lambda ap, tid: effect_baron(game_round, ap, card_played, target_player_id=tid),
            game_round.cancel_played_card_action
        )
        return True

def _resolve_baron_effect(game_round, player, target_player, continuation):
    if not player.hand or not target_player.hand:
        game_round.log_message("So bài Nam tước cần cả hai người chơi đều có bài. Hiệu ứng mất.")
        if continuation: continuation()
        return

    player_card = player.hand[0]; opponent_card = target_player.hand[0]
    winner, loser = (player, target_player) if player_card.value > opponent_card.value else \
                    (target_player, player) if opponent_card.value > player_card.value else (None, None)

    outcome = 'win' if winner == player else 'loss' if loser == player else 'tie'
    details = {'player_card': player_card, 'opponent_card': opponent_card}
    def final_logic():
        if loser:
            game_round.log_message(f"So bài Nam tước: {player.name}({player_card.value}) vs {target_player.name}({opponent_card.value}). {loser.name} bị loại.")
            game_round.eliminate_player(loser, continuation)
        else:
            game_round.log_message(f"So bài Nam tước: {player.name}({player_card.value}) vs {target_player.name}({opponent_card.value}). Hòa!")
            if continuation: continuation()

    animation_data = _prepare_animation_data(player, target_player, CARD_PROTOTYPES['Baron'], outcome, details)
    game_round.ui['animate_card_effect_callback'](animation_data, final_logic)


# --- Handmaid Effect ---

def effect_handmaid(game_round, acting_player, card_played, **kwargs):
    if 'confirmed' in kwargs:
        _resolve_handmaid_effect(game_round, acting_player, game_round.finish_effect_and_proceed)
        return True

    if acting_player.is_cpu:
        _resolve_handmaid_effect(game_round, acting_player, game_round.finish_effect_and_proceed)
        return True
    else:
        game_round.ui['request_confirmation_popup_callback'](
            acting_player, card_played,
            lambda ap: effect_handmaid(game_round, ap, card_played, confirmed=True),
            game_round.cancel_played_card_action
        )
        return True

def _resolve_handmaid_effect(game_round, player, continuation):
    def final_logic():
        player.is_protected = True
        game_round.log_message(f"{player.name} chơi Cô hầu và được bảo vệ.")
        game_round.ui['update_ui_full_callback']()
        if continuation: continuation()

    animation_data = _prepare_animation_data(player, player, CARD_PROTOTYPES['Handmaid'], 'neutral', {})
    game_round.ui['animate_card_effect_callback'](animation_data, final_logic)


# --- Prince Effect ---

def effect_prince(game_round, acting_player, card_played, **kwargs):
    valid_targets = []
    if acting_player.sycophant_target_self:
        if not acting_player.is_eliminated: valid_targets = [acting_player]
        if not valid_targets:
            game_round.log_message(f"Hoàng tử (Kẻ nịnh bợ): {acting_player.name} phải tự chọn mình nhưng không hợp lệ. Hiệu ứng mất.")
            return False
    else:
        valid_targets = _get_generic_targets(game_round, acting_player, include_self=True, unprotected_only=True, allow_no_hand=True)
    if not valid_targets:
        game_round.log_message("Hoàng tử: Không có mục tiêu hợp lệ.")
        return False

    if 'target_player_id' in kwargs:
        target_player = next(p for p in game_round.players if p.id == kwargs['target_player_id'])
        game_round.log_message(f"{acting_player.name} (Hoàng tử) chọn {target_player.name} để bỏ bài và rút.")
        _resolve_prince_effect(game_round, target_player, game_round.finish_effect_and_proceed)
        return True

    if acting_player.is_cpu:
        target_player = random.choice(valid_targets)
        game_round.log_message(f"Máy ({acting_player.name}) chơi Hoàng tử, chọn {target_player.name}.")
        _resolve_prince_effect(game_round, target_player, game_round.finish_effect_and_proceed)
        return True
    else:
        game_round.ui['request_target_selection_callback'](
            acting_player, card_played, valid_targets,
            lambda ap, tid: effect_prince(game_round, ap, card_played, target_player_id=tid),
            game_round.cancel_played_card_action
        )
        return True

def _resolve_prince_effect(game_round, target_player, continuation):
    if not target_player.hand and not game_round.shared_burned_card_ref['card'] and game_round.deck.is_empty():
        game_round.log_message(f"{target_player.name} không có bài và không có lá nào để rút (Hoàng tử).")
        if continuation: continuation()
        return

    discarded_card = target_player.hand[0] if target_player.hand else None
    is_princess = discarded_card and game_round.is_card_in_current_deck('Princess') and discarded_card.name == 'Princess'
    outcome = 'eliminated' if is_princess else 'neutral'
    details = {'discarded_card': discarded_card}

    def final_logic():
        if is_princess:
            game_round.log_message(f"{target_player.name} đã bỏ Công chúa (bị ép bởi Hoàng tử) và bị loại!")
            if game_round.ui.get('add_to_global_discard_callback'): game_round.ui['add_to_global_discard_callback'](target_player, discarded_card)
            target_player.force_discard(game_round, draw_new=False)
            game_round.eliminate_player(target_player, continuation)
        else:
            if discarded_card:
                game_round.log_message(f"{target_player.name} bị buộc phải bỏ lá {discarded_card.name} và rút một lá mới.")
                if game_round.ui.get('add_to_global_discard_callback'): game_round.ui['add_to_global_discard_callback'](target_player, discarded_card)
                target_player.force_discard(game_round, draw_new=True)
            else: # Target had no hand, just draws
                game_round.log_message(f"{target_player.name} không có bài, rút một lá mới.")
                new_card = game_round.draw_from_deck_or_burned()
                if new_card: target_player.add_card_to_hand(new_card)

            if continuation: continuation()

    current_player = game_round.players[game_round.current_player_idx]
    animation_data = _prepare_animation_data(current_player, target_player, CARD_PROTOTYPES['Prince'], outcome, details)
    game_round.ui['animate_card_effect_callback'](animation_data, final_logic)


# --- King Effect ---

def effect_king(game_round, acting_player, card_played, **kwargs):
    valid_targets = _get_generic_targets(game_round, acting_player)
    if acting_player.sycophant_target_self:
        game_round.log_message(f"Kẻ nịnh bợ: {acting_player.name} phải tự chọn mình, nhưng Vua không thể. Hiệu ứng mất.")
        return False
    if not valid_targets:
        game_round.log_message("Vua: Không có mục tiêu hợp lệ.")
        return False

    if 'target_player_id' in kwargs:
        target_player = next(p for p in game_round.players if p.id == kwargs['target_player_id'])
        _resolve_king_effect(game_round, acting_player, target_player, game_round.finish_effect_and_proceed)
        return True

    if acting_player.is_cpu:
        target_player = random.choice(valid_targets)
        _resolve_king_effect(game_round, acting_player, target_player, game_round.finish_effect_and_proceed)
        return True
    else:
        game_round.ui['request_target_selection_callback'](
            acting_player, card_played, valid_targets,
            lambda ap, tid: effect_king(game_round, ap, card_played, target_player_id=tid),
            game_round.cancel_played_card_action
        )
        return True

def _resolve_king_effect(game_round, player, target_player, continuation):
    if not player.hand or not target_player.hand:
        game_round.log_message("Tráo bài Vua cần cả hai người chơi đều có bài. Hiệu ứng mất.")
        if continuation: continuation()
        return

    p_card, o_card = player.hand[0], target_player.hand[0]

    def perform_swap_animation():
        def final_logic():
            player.hand[0], target_player.hand[0] = o_card, p_card # Actual swap
            log_details = f"{player.name} (Vua) tráo bài với {target_player.name}. {player.name} nhận {o_card.name}, {target_player.name} nhận {p_card.name}."
            game_round.log_message(log_details)
            if continuation: continuation()
        game_round.ui['animate_king_swap_callback'](player, target_player, p_card, o_card, final_logic)

    animation_data = _prepare_animation_data(player, target_player, CARD_PROTOTYPES['King'], 'neutral', {})
    game_round.ui['animate_card_effect_callback'](animation_data, perform_swap_animation)


# --- Countess Effect ---

def effect_countess(game_round, acting_player, card_played, **kwargs):
    if 'confirmed' in kwargs:
        _resolve_countess_effect(game_round, acting_player)
        game_round.finish_effect_and_proceed()
        return True

    if acting_player.is_cpu:
        _resolve_countess_effect(game_round, acting_player)
        return False
    else:
        game_round.ui['request_confirmation_popup_callback'](
            acting_player, card_played,
            lambda ap: effect_countess(game_round, ap, card_played, confirmed=True),
            game_round.cancel_played_card_action
        )
        return True

def _resolve_countess_effect(game_round, player):
    game_round.log_message("Nữ Bá tước được chơi. Không có hiệu ứng đặc biệt.")


# --- Princess Effect ---

def effect_princess(game_round, acting_player, card_played, **kwargs):
    # This effect is passive. The check is in GameRound._handle_card_played_logic.
    # This function is here for completeness but should not be called.
    game_round.log_message(f"LỖI: Hiệu ứng Công chúa đã được thực thi, đáng lẽ phải bị chặn sớm hơn.")
    return False

# --- Passive/Placeholder Effects for new cards ---
# These cards have passive effects or effects not yet implemented.
# They don't require user input, so they return False.

def effect_assassin(game_round, acting_player, card_played, **kwargs):
    game_round.log_message("Sát thủ được chơi. Không có hiệu ứng khi tự chơi.")
    return False

def effect_jester(game_round, acting_player, card_played, **kwargs):
    game_round.log_message("Hiệu ứng Tên hề chưa được cài đặt.")
    return False

def effect_cardinal(game_round, acting_player, card_played, **kwargs):
    game_round.log_message("Hiệu ứng Hồng y chưa được cài đặt.")
    return False

def effect_baroness(game_round, acting_player, card_played, **kwargs):
    game_round.log_message("Hiệu ứng Nữ nam tước chưa được cài đặt.")
    return False

def effect_sycophant(game_round, acting_player, card_played, **kwargs):
    game_round.log_message("Hiệu ứng Kẻ nịnh bợ chưa được cài đặt.")
    return False

def effect_count(game_round, acting_player, card_played, **kwargs):
    game_round.log_message("Bá tước được chơi. Hiệu ứng của nó là bị động.")
    return False

def effect_sheriff(game_round, acting_player, card_played, **kwargs):
    game_round.log_message("Nguyên soái được chơi. Hiệu ứng của nó là bị động.")
    return False

def effect_queen_mother(game_round, acting_player, card_played, **kwargs):
    game_round.log_message("Hiệu ứng Nữ hoàng chưa được cài đặt.")
    return False

def effect_bishop(game_round, acting_player, card_played, **kwargs):
    game_round.log_message("Hiệu ứng Giám mục chưa được cài đặt.")
    return False

