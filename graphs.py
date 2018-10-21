from ec import *
from regexes import *
import dill
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plot
from matplotlib.ticker import MaxNLocator
import matplotlib.lines as mlines

import matplotlib
#from test_unpickle import loadfun
def loadfun(x):
    with open(x, 'rb') as handle:
        result = dill.load(handle)
    return result

TITLEFONTSIZE = 14
TICKFONTSIZE = 12
LABELFONTSIZE = 14

matplotlib.rc('xtick', labelsize=TICKFONTSIZE)
matplotlib.rc('ytick', labelsize=TICKFONTSIZE)


class Bunch(object):
    def __init__(self, d):
        self.__dict__.update(d)

    def __setitem__(self, key, item):
        self.__dict__[key] = item

    def __getitem__(self, key):
        return self.__dict__[key]


relu = 'relu'
tanh = 'tanh'
sigmoid = 'sigmoid'
DeepFeatureExtractor = 'DeepFeatureExtractor'
LearnedFeatureExtractor = 'LearnedFeatureExtractor'
TowerFeatureExtractor = 'TowerFeatureExtractor'


def parseResultsPath(p):
    def maybe_eval(s):
        try:
            return eval(s)
        except BaseException:
            return s

    p = p[:p.rfind('.')]
    domain = p[p.rindex('/') + 1: p.index('_')]
    rest = p.split('_')[1:]
    if rest[-1] == "baselines":
        rest.pop()
    parameters = {ECResult.parameterOfAbbreviation(k): maybe_eval(v)
                  for binding in rest
                  for [k, v] in [binding.split('=')]}
    parameters['domain'] = domain
    return Bunch(parameters)


def plotECResult(
        resultPaths,
        colors='rgbycm',
        labels=None,
        title=None,
        export=None,
        showSolveTime=True,
        showTraining=False,
        iterations=None):
    results = []
    parameters = []
    for j, path in enumerate(resultPaths):
        result = loadfun(path)
        print("loaded path:", path)

        if hasattr(result, "baselines") and result.baselines:
            for name, res in result.baselines.items():
                results.append(res)
                p = parseResultsPath(path)
                p["baseline"] = name.replace("_", " ")
                parameters.append(p)
        else:
            results.append(result)
            parameters.append(parseResultsPath(path))

    # Collect together the timeouts, which determine the style of the line
    # drawn
    timeouts = sorted(set(r.enumerationTimeout for r in parameters),
                      reverse=2)
    timeoutToStyle = {
        size: style for size, style in zip(
            timeouts, [
                "-", "--", "-."])}

    f, a1 = plot.subplots(figsize=(4, 3))
    a1.set_xlabel('Iteration', fontsize=LABELFONTSIZE)
    a1.xaxis.set_major_locator(MaxNLocator(integer=True))

    if showSolveTime:
        a1.set_ylabel('%  Solved (solid)', fontsize=LABELFONTSIZE)
        a2 = a1.twinx()
        a2.set_ylabel('Solve time (dashed)', fontsize=LABELFONTSIZE)
    else:
        if not showTraining:
            a1.set_ylabel('% Testing Tasks Solved', fontsize=LABELFONTSIZE)
        else:
            a1.set_ylabel('% Tasks Solved', fontsize=LABELFONTSIZE)
            

    n_iters = max(len(result.learningCurve) for result in results)
    if iterations and n_iters > iterations:
        n_iters = iterations

    plot.xticks(range(0, n_iters), fontsize=TICKFONTSIZE)

    recognitionToColor = {False: "teal", True: "darkorange"}

    for result, p in zip(results, parameters):
        if hasattr(p, "baseline") and p.baseline:
            ys = [100. * result.learningCurve[-1] /
                  len(result.taskSolutions)] * n_iters
        elif showTraining:
            ys = [t/float(len(result.taskSolutions))
                  for t in result.learningCurve[:iterations]]
        else:
            ys = [100. * len(t) / result.numTestingTasks
                  for t in result.testingSearchTime[:iterations]]
        color = recognitionToColor[p.useRecognitionModel]
        l, = a1.plot(list(range(0, len(ys))), ys, color=color, ls='-')

        if showSolveTime:
            if not showTraining:
                a2.plot(range(len(result.testingSearchTime[:iterations])),
                        [sum(ts) / float(len(ts)) for ts in result.testingSearchTime[:iterations]],
                        color=color, ls='--')
            else:
                a2.plot(range(len(result.searchTimes[:iterations])),
                        [sum(ts) / float(len(ts)) for ts in result.searchTimes[:iterations]],
                        color=color, ls='--')

    a1.set_ylim(ymin=0, ymax=110)
    a1.yaxis.grid()
    a1.set_yticks(range(0, 110, 20))
    plot.yticks(range(0, 110, 20), fontsize=TICKFONTSIZE)

    if showSolveTime:
        a2.set_ylim(ymin=0)
        starting, ending = a2.get_ylim()
        if False:
            # [int(zz) for zz in np.arange(starting, ending, (ending - starting)/5.)])
            a2.yaxis.set_ticks([20 * j for j in range(6)])
        else:
            a2.yaxis.set_ticks([50 * j for j in range(6)])
        for tick in a2.yaxis.get_ticklabels():
            tick.set_fontsize(TICKFONTSIZE)

    if title is not None:
        plot.title(title, fontsize=TITLEFONTSIZE)

    # if label is not None:
    legends = []
    if len(timeouts) > 1:
        legends.append(a1.legend(loc='lower right', fontsize=14,
                                 #bbox_to_anchor=(1, 0.5),
                                 handles=[mlines.Line2D([], [], color='black', ls=timeoutToStyle[timeout],
                                                        label="timeout %ss" % timeout)
                                          for timeout in timeouts]))
    f.tight_layout()
    if export:
        plot.savefig(export)  # , additional_artists=legends)
        if export.endswith('.png'):
            os.system('convert -trim %s %s' % (export, export))
        os.system('feh %s' % export)
    else:
        plot.show()
        

def tryIntegerParse(s):
    try:
        return int(s)
    except BaseException:
        return None


if __name__ == "__main__":
    import sys

    import argparse
    parser = argparse.ArgumentParser(description = "")
    parser.add_argument("checkpoints",nargs='+')
    parser.add_argument("--title","-t",type=str,
                        default="")
    parser.add_argument("--iterations","-i",
                        type=str, default=None)
    parser.add_argument("--names","-n",
                        type=str, default="",
                        help="comma-separated list of names to put on the plot for each checkpoint")
    parser.add_argument("--export","-e",
                        type=str, default=None)
    arguments = parser.parse_args()
    
    plotECResult(arguments.checkpoints,
                 export=arguments.export,
                 title=arguments.title,
                 labels=arguments.names.split(","),
                 iterations=arguments.iterations)
