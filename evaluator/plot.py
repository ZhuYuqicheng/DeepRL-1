
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

def plot_dataset(path, total_steps=1e6, goal=0 ,statistic=None, show=True):
    data = load_dataset(path)
    steps = np.linspace(0,total_steps, len(data[0]))
    fig = plt.figure()
    if statistic is None:
        for sample in data:
            plt.plot(steps, sample)
        plt.plot(steps, [goal] * len(steps), 'k--', label = 'goal reward')
    elif statistic is 'normal':
        mean, low, high = mean_confidance(data)
        plt.plot(steps, mean, label = 'mean')
        plt.fill_between(steps, low, high, facecolor='lightblue', label='std-error')
        plt.plot(steps, [goal] * len(steps), 'k--', label = 'goal reward')
        plt.legend()
    else:
        NotImplementedError
    plt.xlabel('Steps')
    plt.ylabel('Average Reward')
    if show:
        plt.show()
    return fig


def compare_datasets(paths, total_steps=1e6, goal=0, show=True):
    fig = plt.figure()
    for path in paths:
        dataset = load_dataset(path)
        label = os.path.basename(path)[0:4]
        steps = np.linspace(0,total_steps, len(dataset[0]))
        mean, low, high = mean_confidance(dataset)
        plt.plot(steps, mean, label=label)
        plt.fill_between(steps, low, high, alpha=0.2)
        plt.legend()
        plt.xlabel('Steps')
        plt.ylabel('Average Reward')
    plt.plot(steps, [goal] * len(steps), 'k--', label = 'goal reward')
    if show:
        plt.show()
    return fig


if __name__ == '__main__':
    fig = plot_dataset('example.npz', statistic='normal')
    plt.show()