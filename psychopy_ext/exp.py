#!/usr/bin/env python

# Part of the psychopy_ext library
# Copyright 2010-2013 Jonas Kubilius
# The program is distributed under the terms of the GNU General Public License,
# either version 3 of the License, or (at your option) any later version.

"""
A library of helper functions for creating and running experiments.

All experiment-related methods are kept here.
"""

import sys, os, csv, glob, random
from UserDict import DictMixin

import numpy as np
import wx
from psychopy import visual, core, event, info, logging, misc, monitors
from psychopy.data import TrialHandler

# pandas does not come by default with PsychoPy but that should not prevent
# people from running the experiment
try:
    import pandas
except:
    pass

class default_computer:
    """The default computer parameters. Hopefully will form a full class at
    some point.
    """
    recognized = False
    # computer defaults
    root = '.'  # means store output files here
    stereo = False  # not like in Psychopy; this merely creates two Windows
    trigger = 'space'  # hit to start the experiment
    defaultKeys = ['escape', trigger]  # "special" keys
    validResponses = {'0': 0, '1': 1}  # organized as input value: output value
    # monitor defaults
    name = 'default'
    distance = 80
    width = 37.5
    # window defaults
    screen = 0  # default screen is 0
    viewScale = [1,1]

def set_paths(exp_root, computer=default_computer, fmri_rel=''):
    """Set paths to data storage.

    :Args:
        exp_root (str)
            Path to where the main file that starts the program is.

    :Kwargs:
        - computer (Namespace, default: :class:`default_computer`)
            A class with a computer parameters defined, such as the default
            path for storing data, size of screen etc. See
            :class:`default_computer` for an example.
        - fmri_rel (str, default: '')
            A path to where fMRI data and related analyzes should be stored.
            This is useful because fMRI data takes a lot of space so you may
            want to keep it on an external hard drive rather than on Dropbox
            where your scripts might live, for example.

    :Returns:
        paths (dict):
            A dictionary of paths.
    """
    run_tests(computer)
    fmri_root = os.path.join(computer.root, fmri_rel)
    exp_root += '/'
    paths = {
        'root': computer.root,
        'exp_root': exp_root,
        'fmri_root': fmri_root,
        'analysis': os.path.join(exp_root, 'analysis/'),  # where analysis files are stored
        'logs': os.path.join(exp_root, 'logs/'),
        'data': os.path.join(exp_root, 'data/'),
        'data_behav': os.path.join(fmri_root, 'data_behav/'),  # for fMRI behav data
        'data_fmri': os.path.join(fmri_root,'data_fmri/'),
        'data_struct': os.path.join(fmri_root,'data_struct/'),  # anatomical data
        'spm_analysis': os.path.join(fmri_root, 'analysis/'),
        'rec': os.path.join(fmri_root,'reconstruction/'), # CARET reconstructions
        'data_rois': os.path.join(fmri_root,'data_rois/'), # preprocessed and masked data
        'sim': exp_root,  # path for storing simulations of models
        }
    return paths

def run_tests(computer):
    """Runs basic tests before starting the experiment.

    At the moment, it only checks if the computer is recognized and if not,
    it waits for a user confirmation to continue thus preventing from running
    an experiment with incorrect settings, such as stimuli size.

    :Kwargs:
        computer (Namespace)
            A class with a computer parameters defined, such as the default
            path for storing data, size of screen etc. See
            :class:`default_computer` for an example.

    """
    if not computer.recognized:
        resp = raw_input("WARNING: This computer is not recognized.\n"
                "To continue, simply hit Enter (default)\n"
                #"To memorize this computer and continue, enter 'm'\n"
                "To quit, enter 'q'\n"
                "Your choice [C,q]: ")
        while resp not in ['', 'c', 'q']:
            resp = raw_input("Choose between continue (c) and quit (q): ")
        if resp == 'q':
            sys.exit()
        #elif resp == 'm':
            #mac = uuid.getnode()
            #if os.path.isfile('computer.py'):
                #write_head = False
            #else:
                #write_head = True
            #try:
                #dataFile = open(datafile, 'ab')
            #print ("Computer %d is memorized. Remember to edit computer.py"
                   #"file to " % mac


class Experiment(TrialHandler):
    """An extension of an TrialHandler with many useful functions.
    """
    def __init__(self,
                parent=None,
                name='',
                version=0.1,
                extraInfo=None,
                runParams=None,
                instructions={'text': '', 'wait': 0},
                actions=None,
                seed=None,
                nReps=1,
                method='random',
                computer=default_computer,
                dataTypes=None,
                originPath=None,
                ):

        self.parent = parent
        self.name = name
        self.version = version
        self.instructions = instructions
        self.actions=actions
        self.nReps = nReps
        self.method = method
        self.computer = computer
        self.dataTypes = dataTypes
        self.originPath = originPath

        self.signalDet = {False: 'Incorrect', True: 'Correct'}

        # minimal parameters that Experiment expects in extraInfo and runParams
        self.extraInfo = OrderedDict([('subjID', 'subj')])
        self.runParams = OrderedDict([('noOutput', False),
                ('debug', False),
                ('autorun', 0),  # if >0, will autorun at the specified speed
                ('push', False),
                ])
        if extraInfo is not None:
            self.extraInfo.update(extraInfo)
        if runParams is not None:
            self.runParams.update(runParams)

    def setup(self, create_win=True):
        """
        Does all the dirty setup before running the experiment.

        Steps include:
            - Logging file setup (:func:`set_logging`)
            - Creating a :class:`~psychopy.visual.Window` (:func:`create_window`)
            - Creating stimuli (:func:`create_stimuli`)
            - Creating trial structure (:func:`create_trial`)
            - Combining trials into a trial list  (:func:`create_triaList`)
            - Creating a :class:`~psychopy.data.TrialHandler` using the
              defined trialList  (:func:`create_TrialHandler`)

        :Kwargs:
            create_win (bool, default: True)
                If False, a window is not created. This is useful when you have
                an experiment consisting of a couple of separate sessions. For
                the first one you create a window and want everything to be
                presented on that window without closing and reopening it
                between the sessions.
        """
        self.set_logging(self.paths['logs'] + self.extraInfo['subjID'])
        if create_win:  # maybe you have a screen already
            self.create_win(debug=self.runParams['debug'])
        self.create_stimuli()
        self.create_trial()
        self.create_trialList()
        self.set_TrialHandler()
        #dataFileName=self.paths['data']%self.extraInfo['subjID'])

        ## guess participant ID based on the already completed sessions
        #self.extraInfo['subjID'] = self.guess_participant(
            #self.paths['data'],
            #default_subjID=self.extraInfo['subjID'])

        #self.dataFileName = self.paths['data'] + '%s.csv'

    def try_makedirs(self, path):
        """Attempts to create a new directory.

        This function improves :func:`os.makedirs` behavior by printing an
        error to the log file if it fails and entering the debug mode
        (:mod:`pdb`) so that data would not be lost.

        :Args:
            path (str)
                A path to create.
        """
        if not os.path.isdir(path) and path not in ['','.','./']:
            try: # if this fails (e.g. permissions) we will get an error
                os.makedirs(path)
            except:
                logging.error('ERROR: Cannot create a folder for storing data %s' %path)
                # FIX: We'll enter the debugger so that we don't lose any data
                import pdb; pdb.set_trace()
                self.quit()

    def set_logging(self, logname='log.log', level=logging.WARNING):
        """Setup files for saving logging information.

        New folders might be created.

        :Kwargs:
            logname (str, default: 'log.log')
                The log file name.
        """
        sysinfo = info.RunTimeInfo(verbose=True, win=False,
                randomSeed='set:time')
        seed = sysinfo['experimentRandomSeed.string']
        self.seed = int(seed)

        if not self.runParams['noOutput']:
            # add .log if no extension given
            if len(logname.split('.')) < 2: logname += '.log'

            # Setup logging file
            self.try_makedirs(os.path.dirname(logname))
            if os.path.isfile(logname):
                writesys = False  # we already have sysinfo there
            else:
                writesys = True
            self.logFile = logging.LogFile(logname, filemode='a', level=level)

            # Write system information first
            if writesys: self.logFile.write('%s\n' % sysinfo)

        # output to the screen
        logging.console.setLevel(level)

    def create_seed(self, seed=None):
        """
        SUPERSEDED by `psychopy.info.RunTimeInfo`
        Creates or assigns a seed for a reproducible randomization.

        When a seed is set, you can, for example, rerun the experiment with
        trials in exactly the same order as before.

        :Kwargs:
            seed (int, default: None)
                Pass a seed if you already have one.

        :Returns:
            self.seed (int)
        """
        if seed is None:
            try:
                self.seed = np.sum([ord(d) for d in self.extraInfo['date']])
            except:
                self.seed = 1
                logging.warning('No seed provided. Setting seed to 1.')
        else:
            self.seed = seed
        return self.seed

    def _guess_participant(self, data_path, default_subjID='01'):
        """Attempts to guess participant ID (it must be int).

        .. :Warning:: Not usable yet

        First lists all csv files in the data_path, then finds a maximum.
        Returns maximum+1 or an empty string if nothing is found.

        """
        datafiles = glob.glob(data_path+'*.csv')
        partids = []
        #import pdb; pdb.set_trace()
        for d in datafiles:
            filename = os.path.split(d)[1]  # remove the path
            filename = filename.split('.')[0]  # remove the extension
            partid = filename.split('_')[-1]  # take the numbers at the end
            try:
                partids.append(int(partid))
            except:
                logging.warning('Participant ID %s is invalid.' %partid)

        if len(partids) > 0: return '%02d' %(max(partids) + 1)
        else: return default_subjID

    def _guess_runNo(self, data_path, default_runNo = 1):
        """Attempts to guess run number.

        .. :Warning:: Not usable yet

        First lists all csv files in the data_path, then finds a maximum.
        Returns maximum+1 or an empty string if nothing is found.

        """
        if not os.path.isdir(data_path): runNo = default_runNo
        else:
            dataFiles = glob.glob(data_path + '*.csv')
            # Splits file names into ['data', %number%, 'runType.csv']
            allNums = [int(os.path.basename(thisFile).split('_')[1]) for thisFile in dataFiles]

            if allNums == []: # no data files yet
                runNo = default_runNo
            else:
                runNo = max(allNums) + 1
                # print 'Guessing runNo: %d' %runNo

        return runNo

    def get_mon_sizes(self, screen=None):
        """Get a list of resolutions for each monitor.

        Recipe from <http://stackoverflow.com/a/10295188>_

        :Args:
            screen (int, default: None)
                Which screen's resolution to return. If None, the a list of all
                screens resolutions is returned.

        :Returns:
            a tuple or a list of tuples of each monitor's resolutions
        """
        app = wx.App(False)  # create an app if there isn't one and don't show it
        nmons = wx.Display.GetCount()  # how many monitors we have
        mon_sizes = [wx.Display(i).GetGeometry().GetSize() for i in range(nmons)]
        if screen is None:
            return mon_sizes
        else:
            return mon_sizes[screen]

    def create_win(self, debug = False, color = 'DimGray'):
        """Generates a :class:`psychopy.visual.Window` for presenting stimuli.

        :Kwargs:
            - debug (bool, default: False)
                - If True, then the window is half the screen size.
                - If False, then the windon is full screen.
            - color (str, str with a hexadecimal value, or a tuple of 3 values, default: "DimGray')
                Window background color. Default is dark gray. (`See accepted
                color names <http://www.w3schools.com/html/html_colornames.asp>`_
        """
        current_level = logging.getLevel(logging.console.level)
        logging.console.setLevel(logging.ERROR)
        monitor = monitors.Monitor(self.computer.name,
            distance=self.computer.distance,
            width=self.computer.width)
        logging.console.setLevel(current_level)
        res = self.get_mon_sizes(self.computer.screen)
        monitor.setSizePix(res)

        self.win = visual.Window(
            monitor = monitor,
            units = 'deg',
            fullscr = not debug,
            allowGUI = debug, # mouse will not be seen unless debugging
            color = color,
            winType = 'pyglet',
            screen = self.computer.screen,
            viewScale = self.computer.viewScale
        )

    def create_fixation(self, shape='complex', color='black'):
        """Creates a fixation spot.

        :Kwargs:
            - shape: {'dot', 'complex'} (default: 'complex')
                Choose the type of fixation:
                    - dot: a simple fixation dot (.2 deg visual angle)
                    - complex: the 'best' fixation shape by `Thaler et al., 2012
                      <http://dx.doi.org/10.1016/j.visres.2012.10.012>`_ which
                      looks like a combination of s bulls eye and cross hair
                      (outer diameter: .6 deg, inner diameter: .2 deg). Note
                      that it is constructed by superimposing two rectangles on
                      a disk, so if non-uniform background will not be visible.
            - color (str, default: 'black')
                Fixation color.

        """
        if shape == 'complex':
            r1 = .3  # radius of outer circle (degrees)
            r2 = .1  # radius of inner circle (degrees)
            oval = visual.Circle(
                self.win,
                name   = 'oval',
                fillColor  = color,
                lineColor = None,
                radius   = r1,
            )
            center = visual.Circle(
                self.win,
                name   = 'center',
                fillColor  = color,
                lineColor = None,
                radius   = r2,
            )
            cross0 = ThickShapeStim(
                self.win,
                name='cross1',
                lineColor=self.win.color,
                lineWidth=2*r2,
                vertices=[(-r1, 0), (r1, 0)]
                )
            cross90 = ThickShapeStim(
                self.win,
                name='cross1',
                lineColor=self.win.color,
                lineWidth=2*r2,
                vertices=[(-r1, 0), (r1, 0)],
                ori=90
                )
            fixation = GroupStim(stimuli=[oval, cross0, cross90, center],
                                 name='fixation')
            # when color is set, we only want the oval and the center to change
            # so here we override :func:`GroupStim.setColor`
            def _set_complex_fix_col(newColor):
                for stim in fixation.stimuli:
                    if stim.name in ['oval', 'center']:
                        stim.setFillColor(newColor)
            fixation.color = color
            fixation.setFillColor = _set_complex_fix_col
            self.fixation = fixation

        elif shape == 'dot':
            self.fixation = GroupStim(
                stimuli=visual.PatchStim(
                    self.win,
                    name   = 'fixation',
                    color  = 'red',
                    tex    = None,
                    mask   = 'circle',
                    size   = .2,
                ),
                name='fixation')

    def latin_square(self, n=6):
        """
        Generates a Latin square of size n. n must be even.

        Based on
        <http://rintintin.colorado.edu/~chathach/balancedlatinsquares.html>_

        :Kwargs:
            n (int, default: 6)
                Size of Latin square. Should be equal to the number of
                conditions you have.

        .. :note: n must be even. For an odd n, I am not aware of a
                  general method to produce a Latin square.

        :Returns:
            A `numpy.array` with each row representing one possible ordering
            of stimuli.
        """
        if n%2 != 0: sys.exit('n is not even!')

        latin = []
        col = np.arange(1,n+1)

        firstLine = []
        for i in range(n):
            if i%2 == 0: firstLine.append((n-i/2)%n + 1)
            else: firstLine.append((i+1)/2+1)

        latin = np.array([np.roll(col,i-1) for i in firstLine])

        return latin.T

    def make_para(self, n=6):
        """
        Generates a symmetric para file with fixation periods approximately 25%
        of the time.

        :Kwargs:
            n (int, default: 6)
                Size of Latin square. Should be equal to the number of
                conditions you have.
                :note: n must be even. For an odd n, I am not aware of a
                general method to produce a Latin square.

        :Returns:
            A `numpy.array` with each row representing one possible ordering
            of stimuli (fixations are coded as 0).
        """
        latin = self.latin_square(n=n).tolist()
        out = []
        for j, thisLatin in enumerate(latin):
            thisLatin = thisLatin + thisLatin[::-1]
            temp = []
            for i, item in enumerate(thisLatin):
                if i%4 == 0: temp.append(0)
                temp.append(item)
            temp.append(0)
            out.append(temp)

        return np.array(out)

    def create_stimuli(self):
        """
        Define stimuli as a dictionary

        Example::

            self.create_fixation(color='white')
            line1 = visual.Line(self.win, name='line1')
            line2 = visual.Line(self.win, fillColor='DarkRed')
            self.s = {
                'fix': self.fixation,
                'stim1': [visual.ImageStim(self.win, name='stim1')],
                'stim2': GroupStim(stimuli=[line1, line2], name='lines')
                }
        """
        raise NotImplementedError

    def create_trial(self):
        """
        Create a list of events that constitute a trial.

        Example::

            self.trial = [{'dur': .100,
                           'display': self.s['fix'],
                           'func': self.waitEvent},

                           {'dur': .300,
                           'display': self.s['stim1'],
                           'func': self.during_trial},
                           ]
        """
        raise NotImplementedError

    def create_trialList(self):
        """
        Put together trials into a trialList.

        Example::

            OrderedDict([
                ('cond', self.morphInd[mNo]),
                ('name', self.paraTable[self.morphInd[mNo]]),
                ('onset', ''),
                ('dur', self.trialDur),
                ('corrResp', corrResp),
                ('subjResp', ''),
                ('accuracy', ''),
                ('rt', ''),
                ])
        """
        raise NotImplementedError

    def idle_event(self, trialClock=None, eventClock=None,
                  thisTrial=None, thisEvent=None, **kwargs):
        """
        Default idle function for the event.

        Sits idle catching key input of default keys (escape and trigger).

        :Kwargs:
            - trialClock (:class:`psychopy.core.Clock`, default: None)
                A clock that started with the trial
            - eventClock (:class:`psychopy.core.Clock`, default: None)
                A clock that started with the event within the trial
            - thisTrial (dict)
                A dictionary of trial properties
            - thisEvent (dict)
                A dictionary with event properties
        """
        if not isinstance(thisEvent['display'], tuple) and \
        not isinstance(thisEvent['display'], list):
            display = [thisEvent['display']]

        if thisEvent['dur'] == 0:
            self.last_keypress()
            for stim in display: stim.draw()
            self.win.flip()

        else:
            for stim in display: stim.draw()
            self.win.flip()

            while eventClock.getTime() < thisEvent['dur'] and \
            trialClock.getTime() < thisTrial['dur']:# and \
            # globClock.getTime() < thisTrial['onset'] + thisTrial['dur']:
                #self.win.getMovieFrame()
                self.last_keypress()

    def feedback(self, trialClock=None, eventClock=None,
        thisTrial=None, thisEvent=None, allKeys=None, *args, **kwargs):
        """
        Gives feedback:
            - correct: fixation change to green
            - wrong: fixation change to red
        """
        thisResp = allKeys[-1]
        subjResp = self.computer.validResponses[thisResp[0]]
        if not isinstance(thisEvent['display'], tuple) and \
            not isinstance(thisEvent['display'], list):
                display = [thisEvent['display']]

        for stim in display:
            if stim.name == 'fixation':
                orig_color = stim.color
                break
        for stim in display:
            if stim.name == 'fixation':
                if thisTrial['corrResp'] == subjResp:
                    stim.setFillColor('DarkGreen')  # correct response
                else:
                    stim.setFillColor('DarkRed')  # incorrect response
            stim.draw()
        self.win.flip()

        # sit idle
        while eventClock.getTime() < thisEvent['dur']:
            self.last_keypress()

        for stim in display:  # reset fixation color
            if stim.name == 'fixation':
                stim.setFillColor(orig_color)

    def set_autorun(self, trialList):
        """
        Automatically runs experiment by simulating key responses.

        This is just the absolute minimum for autorunning. Best practice would
        be extend this function to simulate responses according to your
        hypothesis.

        :Args:
            trialList (list of dict)
                A list of trial definitions.

        :Returns:
            trialList with ``autoResp`` and ``autoRT`` columns included.
        """
        def rt(mean):
            add = np.random.normal(mean,scale=.2)/self.runParams['autorun']
            return self.trial[0]['dur'] + add

        invValidResp = dict([[v,k] for k,v in self.computer.validResponses.items()])
        sortKeys = sorted(invValidResp.keys())
        invValidResp = OrderedDict([(k,invValidResp[k]) for k in sortKeys])
        # speed up the experiment
        for ev in self.trial:
            ev['dur'] /= self.runParams['autorun']
        self.trialDur /= self.runParams['autorun']

        for trial in trialList:
            # here you could do if/else to assign different values to
            # different conditions according to your hypothesis
            trial['autoResp'] = random.choice(invValidResp.values())
            trial['autoRT'] = rt(.5)
        return trialList


    def set_TrialHandler(self):
        """
        Converts a list of trials into a `~psychopy.data.TrialHandler`,
        finalizing the experimental setup procedure.

        Creates ``self.trialDur`` if not present yet.
        Appends information for autorun.
        """
        if not hasattr(self, 'trialDur'):
            self.trialDur = sum(ev['dur'] for ev in self.trial)
        if self.runParams['autorun']:
            self.trialList = self.set_autorun(self.trialList)
        TrialHandler.__init__(self,
            self.trialList,
            nReps=self.nReps,
            method=self.method,
            dataTypes=self.dataTypes,
            extraInfo=self.extraInfo,
            seed=self.seed,
            originPath=self.originPath,
            name=self.name)

    def run(self):
        """
        Setup and go!
        """
        self.setup()
        self.show_instructions(**self.instructions)
        self.loop_trials(
            datafile=self.paths['data'] + self.extraInfo['subjID'] + '.csv',
            noOutput=self.runParams['noOutput'])
        if self.runParams['push']:
            self.commitpush()

    def autorun(self):
        """
        Automatically runs the experiment just like it would normally work but
        responding automatically (as defined in :func:`self.set_autorun`) and
        at the speed specified by `self.runParams['autorun']` parameter. If
        speed is not specified, it is set to 100.
        """
        self.runParams['autorun'] = 100
        self.run()

    def show_instructions(self, text='', wait=0, wait_stim=None):
        """
        Displays instructions on the screen.

        :Kwargs:
            - text (str, default: '')
                Text to be displayed
            - wait (int, default: 0)
                Seconds to wait after removing the text from the screen after
                hitting a spacebar (or a `computer.trigger`)
            - wait_stim (a psychopy stimuli object or their list, default: None)
                Stimuli to show while waiting after the trigger. This is used
                for showing a fixation spot for people to get used to it.
        """
        # for some graphics drivers (e.g., mine:)
        # draw() command needs to be invoked once
        # before it can draw properly
        visual.TextStim(self.win, text='').draw()
        self.win.flip()

        instructions = visual.TextStim(self.win, text=text,
            color='white', height=20, units='pix', pos=(0,0),
            wrapWidth=30*20)
        instructions.draw()
        self.win.flip()

        if not self.runParams['autorun'] or True:
            thisKey = None
            while thisKey != self.computer.trigger:
                thisKey = self.last_keypress()
            if self.runParams['autorun']:
                wait /= self.runParams['autorun']
        self.win.flip()

        if wait_stim is not None:
            if not isinstance(wait_stim, tuple) and not isinstance(wait_stim, list):
                wait_stim = [wait_stim]
            for stim in wait_stim:
                stim.draw()
            self.win.flip()
        core.wait(wait)  # wait a little bit before starting the experiment

    def loop_trials(self, datafile='data.csv', noOutput=False):
        """
        Iterate over the sequence of trials and events.

        .. note:: In the output file, floats are formatted to 1 ms precision so
                  that output files are nice.

        :Kwargs:
            - datafile (str, default: 'data.csv')
                Data file name to store experiment information and responses.
            - noOutput (bool, default: False)
                If True, the data file will not be written. Useful for checking
                how the experiment looks like and for debugging.

        :Raises:
            :py:exc:`IOError` if `datafile` is not found.
        """
        if not noOutput:
            self.try_makedirs(os.path.dirname(datafile))
            try:
                dfile = open(datafile, 'ab')
                datawriter = csv.writer(dfile, lineterminator = '\n')
            except IOError:
                print('Cannot write to the data file %s!' % datafile)
            else:
                write_head = True

        # set up clocks
        globClock = core.Clock()
        trialClock = core.Clock()
        eventClock = core.Clock()
        trialNo = 0
        # go over the trial sequence
        for thisTrial in self:
            trialClock.reset()
            thisTrial['onset'] = globClock.getTime()
            sys.stdout.write("\rtrial %s" % (trialNo+1))
            sys.stdout.flush()

            # go over each event in a trial
            allKeys = []
            for j, thisEvent in enumerate(self.trial):
                eventClock.reset()
                eventKeys = thisEvent['func'](globClock=globClock,
                    trialClock=trialClock, eventClock=eventClock,
                    thisTrial=thisTrial, thisEvent=thisEvent, j=j, allKeys=allKeys)
                if eventKeys is not None:
                    allKeys += eventKeys
                # this is to get keys if we did not do that during trial
                allKeys += event.getKeys(
                    keyList = self.computer.validResponses.keys(),
                    timeStamped = trialClock)

            thisTrial = self.post_trial(thisTrial, allKeys)
            if self.runParams['autorun'] > 0:  # correct the timing
                try:
                    thisTrial['autoRT'] *= self.runParams['autorun']
                    thisTrial['rt'] *= self.runParams['autorun']
                    thisTrial['onset'] *= self.runParams['autorun']
                except:  # maybe not all keys are present
                    pass

            if not noOutput:
                header = self.extraInfo.keys() + thisTrial.keys()
                if write_head:  # will write the header the first time
                    write_head = self._write_header(datafile, header, datawriter)
                out = self.extraInfo.values() + thisTrial.values()
                # cut down floats to 1 ms precision
                outf = ['%.3f'%i if isinstance(i,float) else i for i in out]
                datawriter.writerow(outf)

            trialNo += 1
        sys.stdout.write("\n")  # finally jump to the next line in the terminal
        if not noOutput: dfile.close()

    def _write_header(self, datafile, header, datawriter):
        """Determines if a header should be writen in a csv data file.

        Works by reading the first line and comparing it to the given header.
        If the header already is present, then a new one is not written.

        :Args:
            - datafile (str)
                Name of the data file
            - header (list of str)
                A list of column names
            - datawriter (:class:`csv.writer`)
                A CSV writer for writing data to the data file

        :Returns:
            False, so that it is never called again during :func:`loop_trials`
        """
        write_head = True
        # no header needed if the file already exists and has one
        try:
            dataf_r = open(datafile, 'rb')
            dataread = csv.reader(dataf_r)
        except:
            pass
        else:
            try:
                header_file = dataread.next()
            except:  # empty file
                write_head = True
            else:
                if header == header_file:
                    write_head = False
                else:
                    write_head = True
            dataf_r.close()
        if write_head:
            datawriter.writerow(header)
        return False

    def last_keypress(self, keyList=None):
        """
        Extract the last key pressed from the event list.

        If escape is pressed, quits.

        :Kwargs:
            keyList (list of str, default: `self.computer.defaultKeys`)
                A list of keys that are recognized. Any other keys pressed will
                not matter.

        :Returns:
            An str of a last pressed key or None if nothing has been pressed.
        """
        if keyList is None:
            keyList = self.computer.defaultKeys
        thisKeyList = event.getKeys(keyList=keyList)
        if len(thisKeyList) > 0:
            thisKey = thisKeyList.pop()
            if thisKey == 'escape':
                print  # because we've been using sys.stdout.write without \n
                self.quit()
            else:
                return thisKey
        else:
            return None

    def wait_for_response(self, RT_clock=False, fakeKey=None):
        """
        Waits for response. Returns last key pressed, timestamped.

        :Kwargs:
            - RT_clock (False or `psychopy.core.Clock`, default: False)
                A clock used as a reference for measuring response time

            - fakeKey (None or a tuple (key pressed, response time), default: None)
                This is used for simulating key presses in order to test that
                the experiment is working.

        :Returns:
            A list of tuples with a key name (str) and a response time (float).

        """
        allKeys = []
        event.clearEvents() # key presses might be stored from before
        while len(allKeys) == 0: # if the participant did not respond earlier
            if fakeKey is not None:
                if RT_clock.getTime() > fakeKey[1]:
                    allKeys = [fakeKey]
            else:
                allKeys = event.getKeys(
                    keyList = self.computer.validResponses.keys(),
                    timeStamped = RT_clock)
            self.last_keypress()
        return allKeys

    def post_trial(self, thisTrial, allKeys):
        """A default function what to do after a trial is over.

        It records the participant's response as the last key pressed,
        calculates accuracy based on the expected (correct) response value,
        and records the time of the last key press with respect to the onset
        of a trial. If no key was pressed, participant's response and response
        time are recorded as an empty string, while accuracy is assigned a
        'No response'.

        :Args:
            - thisTrial (dict)
                A dictionary of trial properties
            - allKeys (list of tuples)
                A list of tuples with the name of the pressed key and the time
                of the key press.

        :Returns:
            thisTrial with ``subjResp``, ``accuracy``, and ``rt`` filled in.

        """
        if len(allKeys) > 0:
            thisResp = allKeys.pop()
            thisTrial['subjResp'] = self.computer.validResponses[thisResp[0]]
            acc = thisTrial['corrResp']==thisTrial['subjResp']
            thisTrial['accuracy'] = self.signalDet[acc]
            thisTrial['rt'] = thisResp[1]
        else:
            thisTrial['subjResp'] = ''
            thisTrial['accuracy'] = ''
            thisTrial['rt'] = ''

        return thisTrial

    def commitpush(self, message=None):
        """
        Add, commit, and push changes to a remote repository.

        TODO: How to set this up.
        """
        if message is None:
            message = 'data for participant %s' % self.extraInfo['subjID']
        rev = self._detect_rev()
        if rev == 'hg':
            cmd = 'hg commit -A -m "%s"' % message
            hg, err = core.shellCall(cmd, stderr=True)
            self.logFile.write('\n'.join((cmd, hg, err)))
            sys.stdout.write('\n'.join((cmd, hg, err)))
            if err == '':
                cmd = 'hg push'
                hg, err = core.shellCall(cmd, stderr=True)
                self.logFile.write('\n'.join((cmd, hg, err)))
                sys.stdout.write('\n'.join((cmd, hg, err)))
        else:
            logging.error('%s revision control is not supported for commiting' %
                           rev)

    def _detect_rev(self):
        """
        Detects revision control system.

        Recognizes: git, hg, svn
        """
        caller = sys.argv[0]
        revs = ['git', 'hg', 'svn']
        for rev in revs:
            revdir = os.path.join(os.path.dirname(caller), '.' + rev)
            if os.path.exists(caller) and os.path.isdir(revdir):
                return rev

    def quit(self):
        """What to do when exit is requested.
        """
        logging.warning('Premature exit requested by user.')
        self.win.close()
        core.quit()
        # redefine core.quit() so that an App window would not be killed
        #logging.flush()
        #for thisThread in threading.enumerate():
            #if hasattr(thisThread,'stop') and hasattr(thisThread,'running'):
                ##this is one of our event threads - kill it and wait for success
                #thisThread.stop()
                #while thisThread.running==0:
                    #pass#wait until it has properly finished polling
        #sys.exit(0)

    def _astype(self,type='pandas'):
        """
        Converts data into a requested type.

        Mostly reused :func:`psychopy.data.TrialHandler.saveAsWideText`

        :Kwargs:
            type
        """
        # collect parameter names related to the stimuli:
        header = self.trialList[0].keys()
        # and then add parameter names related to data (e.g. RT)
        header.extend(self.data.dataTypes)

        # loop through each trial, gathering the actual values:
        dataOut = []
        trialCount = 0
        # total number of trials = number of trialtypes * number of repetitions:
        repsPerType={}
        for rep in range(self.nReps):
            for trialN in range(len(self.trialList)):
                #find out what trial type was on this trial
                trialTypeIndex = self.sequenceIndices[trialN, rep]
                #determine which repeat it is for this trial
                if trialTypeIndex not in repsPerType.keys():
                    repsPerType[trialTypeIndex]=0
                else:
                    repsPerType[trialTypeIndex]+=1
                repThisType=repsPerType[trialTypeIndex]#what repeat are we on for this trial type?

                # create a dictionary representing each trial:
                # this is wide format, so we want fixed information (e.g. subject ID, date, etc) repeated every line if it exists:
                if (self.extraInfo != None):
                    nextEntry = self.extraInfo.copy()
                else:
                    nextEntry = {}

                # add a trial number so the original order of the data can always be recovered if sorted during analysis:
                trialCount += 1
                nextEntry["TrialNumber"] = trialCount

                # now collect the value from each trial of the variables named in the header:
                for parameterName in header:
                    # the header includes both trial and data variables, so need to check before accessing:
                    if self.trialList[trialTypeIndex].has_key(parameterName):
                        nextEntry[parameterName] = self.trialList[trialTypeIndex][parameterName]
                    elif self.data.has_key(parameterName):
                        nextEntry[parameterName] = self.data[parameterName][trialTypeIndex][repThisType]
                    else: # allow a null value if this parameter wasn't explicitly stored on this trial:
                        nextEntry[parameterName] = ''

                #store this trial's data
                dataOut.append(nextEntry)

        # get the extra 'wide' parameter names into the header line:
        header.insert(0,"TrialNumber")
        if (self.extraInfo != None):
            for key in self.extraInfo:
                header.insert(0, key)

        if type in [list, 'list']:
            import pdb; pdb.set_trace()
        elif type in [dict, 'dict']:
            import pdb; pdb.set_trace()
        elif type == 'pandas':
            df = pandas.DataFrame(dataOut, columns=header)

        return df

    def aspandas(self):
        """
        Convert trialList into a pandas DataFrame object
        """
        return self._astype(type='pandas')

    #def accuracy(self):
        #df = self._astype(list)
        #for line in df:
            #if line['accuracy']=='Correct':
                #accuracy += 1
        #acc = accuracy * 100 / len(df)
        #return acc

    def weighted_sample(self, probs):
        if not np.allclose(np.sum(probs), 1):
            raise Exception('Probabilities must add up to one.')
        which = np.random.random()
        ind = 0
        while which>0:
            which -= probs[ind]
            ind +=1
        ind -= 1
        return ind

    def get_behav_df(self, pattern='%s'):
        """
        Extracts data from files for data analysis.

        :Kwargs:
            pattern (str, default: '%s')
                A string with formatter information. Usually it contains a path
                to where data is and a formatter such as '%s' to indicate where
                participant ID should be incorporated.

        :Returns:
            A `pandas.DataFrame` of data for the requested participants.
        """
        if type(self.extraInfo['subjID']) not in [list, tuple]:
            subjID_list = [self.extraInfo['subjID']]
        else:
            subjID_list = self.extraInfo['subjID']

        df_fnames = []
        for subjID in subjID_list:
            df_fnames += glob.glob(pattern % subjID)
        dfs = []
        for dtf in df_fnames:
            data = pandas.read_csv(dtf)
            if data is not None:
                dfs.append(data)
        if dfs == []:
            print df_fnames
            raise IOError('Behavioral data files not found.\n'
                'Tried to look for %s' % (pattern % subjID))
        df = pandas.concat(dfs, ignore_index=True)

        return df


class ThickShapeStim(visual.ShapeStim):
    """
    Draws thick shape stimuli as a collection of lines.

    PsychoPy has a bug in some configurations of not drawing lines thicker
    than 2px. This class fixes the issue. Note that it's really just a
    collection of rectanges so corners will not look nice.
    """
    def __init__(self,
                 win,
                 units  ='',
                 lineWidth=1.0,
                 lineColor=(1.0,1.0,1.0),
                 lineColorSpace='rgb',
                 fillColor=None,
                 fillColorSpace='rgb',
                 vertices=((-0.5,0),(0,+0.5),(+0.5,0)),
                 closeShape=True,
                 pos= (0,0),
                 size=1,
                 ori=0.0,
                 opacity=1.0,
                 depth  =0,
                 interpolate=True,
                 lineRGB=None,
                 fillRGB=None,
                 name='', autoLog=True):

        visual._BaseVisualStim.__init__(self, win, units=units, name=name, autoLog=autoLog)

        self.opacity = opacity
        self.pos = np.array(pos, float)
        self.closeShape=closeShape
        self.lineWidth=lineWidth
        self.interpolate=interpolate

        self._useShaders=False  #since we don't need to combine textures with colors
        self.lineColorSpace=lineColorSpace
        if lineRGB!=None:
            logging.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setLineColor(lineRGB, colorSpace='rgb')
        else:
            self.setLineColor(lineColor, colorSpace=lineColorSpace)

        self.fillColorSpace=fillColorSpace
        if fillRGB!=None:
            logging.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setFillColor(fillRGB, colorSpace='rgb')
        else:
            self.setFillColor(fillColor, colorSpace=fillColorSpace)

        self.depth=depth
        self.ori = np.array(ori,float)
        self.size = np.array([0.0,0.0])
        self.setSize(size)
        self.setVertices(vertices)
        # self._calcVerticesRendered()
        # if len(self.stimulus) == 1: self.stimulus = self.stimulus[0]

    #def __init__(self, *args, **kwargs):
        #try:
            #orig_vertices = kwargs['vertices']
            #kwargs['vertices'] = [(-0.5,0),(0,+0.5)]#,(+0.5,0)),
        #except:
            #pass
        ##import pdb; pdb.set_trace()
        #visual.ShapeStim.__init__(self, *args, **kwargs)
        #self.vertices = orig_vertices

    def draw(self):
        for stim in self.stimulus:
            stim.draw()

    def setOri(self, newOri):
        # theta = (newOri - self.ori)/180.*np.pi
        # rot = np.array([[np.cos(theta), -np.sin(theta)],[np.sin(theta), np.cos(theta)]])
        # for stim in self.stimulus:
            # newVert = []
            # for vert in stim.vertices:
                # #import pdb; pdb.set_trace()
                # newVert.append(np.dot(rot,vert))
            # stim.setVertices(newVert)
        self.ori = newOri
        self.setVertices(self.vertices)

    def setPos(self, newPos):
        #for stim in self.stimulus:
            #stim.setPos(newPos)
        self.pos = newPos
        self.setVertices(self.vertices)

    def setVertices(self, value=None):
        if isinstance(value[0][0], int) or isinstance(value[0][0], float):
            self.vertices = [value]
        else:
            self.vertices = value
        self.stimulus = []

        theta = self.ori/180.*np.pi #(newOri - self.ori)/180.*np.pi
        rot = np.array([[np.cos(theta), -np.sin(theta)],[np.sin(theta), np.cos(theta)]])

        for vertices in self.vertices:
            if self.closeShape: numPairs = len(vertices)
            else: numPairs = len(vertices)-1

            wh = self.lineWidth/2. - misc.pix2deg(1,self.win.monitor)
            for i in range(numPairs):
                thisPair = np.array([vertices[i],vertices[(i+1)%len(vertices)]])
                thisPair_rot = np.dot(thisPair, rot.T)
                edges = [
                    thisPair_rot[1][0]-thisPair_rot[0][0],
                    thisPair_rot[1][1]-thisPair_rot[0][1]
                    ]
                lh = np.sqrt(edges[0]**2 + edges[1]**2)/2.

                line = visual.ShapeStim(
                    self.win,
                    lineWidth   = 1,
                    lineColor   = self.lineColor,#None,
                    interpolate = True,
                    fillColor   = self.lineColor,
                    ori         = -np.arctan2(edges[1],edges[0])*180/np.pi,
                    pos         = np.mean(thisPair_rot,0) + self.pos,
                    # [(thisPair_rot[0][0]+thisPair_rot[1][0])/2. + self.pos[0],
                                   # (thisPair_rot[0][1]+thisPair_rot[1][1])/2. + self.pos[1]],
                    vertices    = [[-lh,-wh],[-lh,wh],
                                   [lh,wh],[lh,-wh]]
                )
                #line.setOri(self.ori-np.arctan2(edges[1],edges[0])*180/np.pi)
                self.stimulus.append(line)


class GroupStim(object):

    def __init__(self, stimuli=None, name=None):
        if not isinstance(stimuli, tuple) and not isinstance(stimuli, list):
            self.stimuli = [stimuli]
        else:
            self.stimuli = stimuli
        if name is None:
            self.name = self.stimuli[0].name
        else:
            self.name = name

    def __getattr__(self, name):
        """Do whatever asked but per stimulus
        """
        def method(*args, **kwargs):
            outputs =[getattr(stim, name)(*args, **kwargs) for stim in self.stimuli]
            # see if only None returned, meaning that probably the function
            # doesn't return anything
            notnone = [o for o in outputs if o is not None]
            if len(notnone) != 0:
                return outputs
        try:
            return method
        except TypeError:
            return getattr(self, name)

    def __iter__(self):
        return self.stimuli.__iter__()


class OrderedDict(dict, DictMixin):
    """
    OrderedDict code (because some are stuck with Python 2.5)

    Produces an dictionary but with (key, value) pairs in the defined order.

    Created by Raymond Hettinger on Wed, 18 Mar 2009, under the MIT License
    <http://code.activestate.com/recipes/576693/>_
    """
    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))
        try:
            self.__end
        except AttributeError:
            self.clear()
        self.update(*args, **kwds)

    def clear(self):
        self.__end = end = []
        end += [None, end, end]         # sentinel node for doubly linked list
        self.__map = {}                 # key --> [key, prev, next]
        dict.clear(self)

    def __setitem__(self, key, value):
        if key not in self:
            end = self.__end
            curr = end[1]
            curr[2] = end[1] = self.__map[key] = [key, curr, end]
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        key, prev, next = self.__map.pop(key)
        prev[2] = next
        next[1] = prev

    def __iter__(self):
        end = self.__end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.__end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def popitem(self, last=True):
        if not self:
            raise KeyError('dictionary is empty')
        if last:
            key = reversed(self).next()
        else:
            key = iter(self).next()
        value = self.pop(key)
        return key, value

    def __reduce__(self):
        items = [[k, self[k]] for k in self]
        tmp = self.__map, self.__end
        del self.__map, self.__end
        inst_dict = vars(self).copy()
        self.__map, self.__end = tmp
        if inst_dict:
            return (self.__class__, (items,), inst_dict)
        return self.__class__, (items,)

    def keys(self):
        return list(self)

    setdefault = DictMixin.setdefault
    update = DictMixin.update
    pop = DictMixin.pop
    values = DictMixin.values
    items = DictMixin.items
    iterkeys = DictMixin.iterkeys
    itervalues = DictMixin.itervalues
    iteritems = DictMixin.iteritems

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, self.items())

    def copy(self):
        return self.__class__(self)

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d

    def __eq__(self, other):
        if isinstance(other, OrderedDict):
            return len(self)==len(other) and self.items() == other.items()
        return dict.__eq__(self, other)

    def __ne__(self, other):
        return not self == other

def combinations(iterable, r):
    """
    Produces combinations of `iterable` elements of lenght `r`.

    Examples:
        - combinations('ABCD', 2) --> AB AC AD BC BD CD
        - combinations(range(4), 3) --> 012 013 023 123

    `From Python 2.6 docs <http://docs.python.org/library/itertools.html#itertools.combinations>`_
    under the Python Software Foundation License

    :Args:
        - iterable
            A list-like or a str-like object that contains some elements
        - r
            Number of elements in each ouput combination

    :Returns:
        A generator yielding combinations of lenght `r`
    """
    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    indices = range(r)
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            return
        indices[i] += 1
        for j in range(i+1, r):
            indices[j] = indices[j-1] + 1
        yield tuple(pool[i] for i in indices)

def combinations_with_replacement(iterable, r):
    """
    Produces combinations of `iterable` elements of length `r` with
    replacement: identical elements can occur in together in some combinations.

    Example: combinations_with_replacement('ABC', 2) --> AA AB AC BB BC CC

    `From Python 2.6 docs <http://docs.python.org/library/itertools.html#itertools.combinations_with_replacement>`_
    under the Python Software Foundation License

    :Args:
        - iterable
            A list-like or a str-like object that contains some elements
        - r
            Number of elements in each ouput combination

    :Returns:
        A generator yielding combinations (with replacement) of length `r`
    """
    pool = tuple(iterable)
    n = len(pool)
    if not n and r:
        return
    indices = [0] * r
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != n - 1:
                break
        else:
            return
        indices[i:] = [indices[i] + 1] * (r - i)
        yield tuple(pool[i] for i in indices)
