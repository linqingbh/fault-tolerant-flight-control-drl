import warnings
import signal

import pandas as pd
from agent.sac import SAC
from agent.policy import LnMlpPolicy
from agent.callback import SaveOnBestReturn

from envs.citation_rates import Citation
from tools.schedule import schedule
from tools.identifier import get_ID
from tools.plot_training import plot_training
from tools.plot_response import get_response
from get_task import get_task

warnings.filterwarnings("ignore", category=FutureWarning, module='tensorflow')
warnings.filterwarnings("ignore", category=UserWarning, module='gym')


# > LESS NOISY POLICY
# todo: tune penalty
# ? control input as deflection angle derivative

# > NOT LEARNING
# todo: change network width
# todo: give more observations
# ? change reward function


def learn():

    env_train = Citation(task=get_task()[:3], time_vector=get_task()[3])
    env_eval = Citation(task=get_task()[:3], time_vector=get_task()[3])

    callback = SaveOnBestReturn(eval_env=env_eval, eval_freq=2000, log_path="agent/trained/tmp/",
                                best_model_save_path="agent/trained/tmp/")
    agent = SAC(LnMlpPolicy, env_train, verbose=1,
                ent_coef='auto', batch_size=256,
                learning_rate=schedule(0.0004, 0.0002)
                )
    agent.learn(total_timesteps=int(5e6), log_interval=50, callback=callback)
    agent = SAC.load("agent/trained/tmp/best_model.zip")
    ID = get_ID(6)
    agent.save(f'agent/trained/{get_task()[4]}_{ID}.zip')
    training_log = pd.read_csv('agent/trained/tmp/monitor.csv')
    training_log.to_csv(f'agent/trained/{get_task()[4]}_{ID}.csv')
    plot_training(ID, get_task()[4])
    get_response(env_eval, agent=agent, ID=ID)

    return


def run_preexisting(ID=None, directory: str = 'tmp'):

    env_eval = Citation(task=get_task()[:3], time_vector=get_task()[3])
    agent = SAC.load(f"agent/trained/{directory}/best_model.zip")

    if ID is None:
        get_response(env_eval, agent=agent)
    else:
        get_response(env_eval, agent=agent, ID=ID)


def keyboardInterruptHandler(signal, frame):
    print('')
    print('Early stopping. Getting last results...')
    run_preexisting()
    exit(0)


signal.signal(signal.SIGINT, keyboardInterruptHandler)
learn()
# run_preexisting()
# run_pre existing('5DVX67')

# os.system('say "your program has finished"')
