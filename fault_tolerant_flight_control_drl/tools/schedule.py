import math


def constant(initial_value):
    """
    Constant learning rate schedule.

    :param initial_value: (float or str)
    :return: (function)
    """
    def func(progress):
        """
        Progress will decrease from 1 (beginning) to 0
        :param progress: (float)
        :return: (float)
        """
        return initial_value

    return func


def schedule(initial_value):
    """
    Linear learning rate schedule.

    :param initial_value: (float or str)
    :return: (function)
    """

    def func(progress):
        """
        Progress will decrease from 1 (beginning) to 0
        :param progress: (float)
        :return: (float)
        """
        return progress * initial_value

    return func


def schedule_kink(initial_value, second_value):
    """
    Linear learning rate schedule with kink.

    :param initial_value: (float or str)
    :param second_value: (float or str)
    :return: (function)
    """

    def func(progress):
        """
        Progress will decrease from 1 (beginning) to 0
        :param progress: (float)
        :return: (float)
        """
        if progress < 0.5:
            return progress * initial_value + 0
        else:
            return progress * second_value + 1e-4

    return func


def schedule_exp(initial_value):
    """
    Exponential decay learning rate schedule.

    :param initial_value: (float or str)
    :return: (function)
    """

    def func(progress):
        """
        Progress will decrease from 1 (beginning) to 0
        :param progress: (float)
        :return: (float)
        """
        k = 2.0
        return initial_value * math.exp(-k * progress)

    return func
