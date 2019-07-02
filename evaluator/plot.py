
import os
import numpy as np 
import matplotlib.pyplot as plt
from evaluator.statistics import mean_confidance

def load_dataset(path):
    if os.path.isfile(path):
            data = np.array([array for array in np.load(path).values()])
            return data
    else:
        raise FileNotFoundError

def plot_dataset(path, step=5000, goal=0 ,statistic=None, show=True):
    data = load_dataset(path)
    steps = len(data[0]) * step
    fig = plt.figure()
    if statistic is None:
        for sample in data:
            plt.plot(sample)
        plt.plot([goal] * steps, 'k--', label = 'goal reward')
    elif statistic is 'normal':
        mean, low, high = mean_confidance(data)
        plt.plot(mean, label = 'mean')
        plt.fill_between(range(steps), low, high, facecolor='lightblue', label='std-error')
        plt.plot([goal] * steps, 'k--', label = 'goal reward')
        plt.legend()
    else:
        NotImplementedError
    plt.xlabel('Steps')
    plt.ylabel('Average Reward')
    if show:
        plt.show()
    return fig


if __name__ == '__main__':
    fig = plot_dataset('example.npz', statistic='normal')
    plt.show()
