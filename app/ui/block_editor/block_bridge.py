"""
Bridge between core Step dataclasses and UI block widgets.
"""
from __future__ import annotations
from typing import Optional

from app.core.models import (
    Step, ActionStep, ConditionStep, DelayStep,
    BranchStep, LoopStep, SetVariableStep, CallScenarioStep,
)


def step_to_block(step: Step) -> Optional["BaseBlock"]:
    """Convert a core Step → the matching UI block widget."""
    from app.ui.block_editor.blocks.action_block import ActionBlock
    from app.ui.block_editor.blocks.delay_block import DelayBlock
    from app.ui.block_editor.blocks.condition_block import ConditionBlock
    from app.ui.block_editor.blocks.branch_block import BranchBlock
    from app.ui.block_editor.blocks.loop_block import LoopBlock
    from app.ui.block_editor.blocks.variable_block import VariableBlock
    from app.ui.block_editor.blocks.call_block import CallBlock

    if isinstance(step, ActionStep):
        block = ActionBlock(step.action_type.value)
        block.from_step(step)
        return block
    if isinstance(step, DelayStep):
        block = DelayBlock()
        block.from_step(step)
        return block
    if isinstance(step, ConditionStep):
        block = ConditionBlock()
        block.from_step(step)
        return block
    if isinstance(step, BranchStep):
        block = BranchBlock()
        block.from_step(step)
        return block
    if isinstance(step, LoopStep):
        block = LoopBlock()
        block.from_step(step)
        return block
    if isinstance(step, SetVariableStep):
        block = VariableBlock()
        block.from_step(step)
        return block
    if isinstance(step, CallScenarioStep):
        block = CallBlock()
        block.from_step(step)
        return block
    return None
