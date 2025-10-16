# coding: utf-8


import tomoscan.progress


def test_progress():
    """Simple test of the Progress API"""
    progress = tomoscan.progress.Progress("this is progress")
    progress.reset()
    progress.startProcess()
    progress.setMaxAdvancement(80)
    for adv in (10, 20, 50, 70):
        progress.setAdvancement(adv)
    for _ in range(10):
        progress.increaseAdvancement(1)


def test_advancement():
    """Simple test of the _Advancement API"""
    for i in range(4):
        tomoscan.progress._Advancement.getNextStep(
            tomoscan.progress._Advancement.getStep(i)
        )
