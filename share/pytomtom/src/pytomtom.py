#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
pyTOMTOM - Manage your TomTom!
http://pytomtom.tuxfamily.org

Copyright (c) 2009-2011: Thomas LEROY

Licence:
  GPL v3

Depends:
  python (>=2.5), python-gtk2, cabextract, ImageMagick

Follow PEP 8: Style Guide for Python
  http://www.python.org/dev/peps/pep-0008
'''

# Ensure Python 2.5 compatibility
from __future__ import with_statement

import gtk
import urllib2
import webbrowser
import subprocess
import shutil
import os
import os.path
import getopt
import sys
import gettext
import tempfile
import gobject
import random

# Used to get terminal width
import termios
import fcntl
import struct

from datetime import date

APP = 'pyTOMTOM'
VER = '0.6 alpha 1'
WEB_URL = 'http://pytomtom.tuxfamily.org'

# i18n (internationalisation) /usr/share/locale
gettext.bindtextdomain('pytomtom', '../share/locale')
gettext.textdomain('pytomtom')
_ = gettext.gettext

# TODO: In non-text mode launched from a terminal, an error message
# happens. It does not prevent to launch the application nor its
# functionalities, but it would be cleaner do avoid it.
# BC: Need more details about that issue in order to fix it.

# Only Linux is supported so far, so exit if the OS is not posix
# compliant
if os.name != 'posix':
    print 'You are not runnig Linux operating system'
    sys.exit(2)


class NotebookTomtom:

    # config directory
    dir = os.getenv('HOME') + '/.' + APP
    # config file
    config_file = APP + '.cfg'
    # ephem directory on tomtom
    dest = '/ephem'
    # poi database directory
    dir_poi = dir + '/poi/'
    # backup directory
    dir_backup = dir + '/backup'
    # file needed for recognize a tomtom
    ttgo = '/tomtom.ico'
    # pix directory (for pytomtom)
    dir_pix = '../share/pytomtom/pix/'
    # mount point, false = unknow
    mount = False
    # mount point size (octet)
    pt_mount_size = -1
    # all mount points, by default empty
    pt_mounts = []
    # tomtom model, false = unknow
    model = False
    # current map in use, false = unknow
    current_map = False
    # tab at pytomtom start, by default "About"
    # 0=options, 1=GPSQuickFix, 2=Save&Restore, 3=poi, 4=personalize, 5=about, 6=quit
    box_init = 5
    # chipset siRFStarIII models
    si_rfstar_iii = [
        'Carminat',
        'GO 300',
        'GO 500',
        'GO 510',
        'GO 520',
        'GO 530',
        'GO 540 LIVE',
        'GO 630',
        'GO 700',
        'GO 710',
        'GO 720',
        'GO 730',
        'GO 910',
        'GO 920',
        'GO 930',
        'ONE 1st Edition',
        'ONE 2nd Edition (S)',
        'RIDER',
        'RIDER 2nd Edition',
        ]
    # chipset globalLocate models
    global_locate = [
        'GO 740 LIVE',
        'GO 750 LIVE',
        'GO 940 LIVE',
        'GO 950 LIVE',
        'GO LIVE 820',
        'GO LIVE 825',
        'GO Live 1000',
        'GO Live 1005',
        'ONE 2nd Edition (G)',
        'ONE 3rd Edition',
        'ONE 30 Series',
        'ONE 130',
        'ONE IQ Routes',
        'ONE White Pearl',
        'ONE XL',
        'Start',
        'Start 2',
        'Via 110',
        'Via 120',
        'Via 125',
        'XL 30 Series',
        'XL IQ Routes',
        'XL LIVE IQ Routes',
        ]
    # all models
    # TODO : not use append, extend instead ?
    models = []
    for model in si_rfstar_iii:
        models.append(model)
    for model in global_locate:
        models.append(model)
    # alphabetic sort
    models.sort()

    # log level, =< 1 by default
    log_level = 1

    # log, sys.stdout (= print)
    log_file_name = dir + '/' + os.path.basename(sys.argv[0]) + '.log'
    # ie : logFile = open( logFileName, "w" ) # erase an write new
    # ie : logFile = open( logFileName, "a" ) # add and write
    # = print
    log_file = sys.stdout

    # by default log isn't overwrited, this option to overwrite log
    overwrite_log = False
    # launching without gui (script mode), false by default
    no_gui = False
    # launching witout do external action (to log_level, ie gpsquickfix, backup, restore)
    no_exec = False
    # launch GPSQuickFix
    do_gps_fix = False
    # launch backup
    do_backup = False
    # launch save
    do_save = False
    # launch restore
    do_restore = False
    # backup or restore launched process
    proc_backup = None
    # filename for restore or backup
    file_name = False
    # progression bar for restore or backup
    progression_bar = None
    # progression bar size for gui (in text mode, size is calculated /terminal)
    progression_bar_size = 120
    # estimated time remind
    config_time_remind = True
    # time passed
    config_time_passed = False
    # estimated total time
    config_time_tot = True
    # tempo for progress bar
    tempo = None
    # tempo delay for progress bar
    tempo_delay = 3000
    # timestamp at start, to calculate estimated time remind and estimated total time
    tempo_start_time = None
    # minuteur pour le refraichissement du combo contenant la liste des points de montages
    tempo_combo = None
    # Verification de la possibilite d'effectuer le GPSFix (presence de cabextract)
    could_gps_fix = True
    # Verification de la possibilite d'effectuer le backup (presence de tar)
    could_backup = True
    # Si l'utilisateur veut quitter avant la fin d'un sous-processus, la sauvegarde ou la restauration finissent puis l'application quitte
    quit = False
    # gps status at start
    gps_status = 'disconnected'

    # objet graphique window
    window = None
    # objet graphique de la liste des points de montage
    pt_combo = None


    def debug(self, niveau, text):
        '''Fonction d'affichage des informations

        '''
        # Affichage uniquement si le niveau general de debug est superieur au niveau du debug fourni
        if niveau <= self.log_level:
            # Ecriture dans le fichier de log
            self.log_file.write(str(date.today()) + ' ' + text + '\n')
            # flush pour un affichage immediat
            self.log_file.flush()
        return True

    def print_version(self):
        ''' Fonction d'affichage du nom et de la version de l'application

        '''

        print ''
        print APP
        print VER

    def recup(self):
        '''conversion pyTOMTOM to pytomtom (=< 0.4.2 to 0.5)
           later, we'll suppress this... (or not)

        '''

        # old config directory
        old_dir = os.getenv('HOME') + '/.pyTOMTOM'
        if not os.path.exists(self.dir):
            # new config directory if not exist
            os.mkdir(self.dir)
        if os.path.exists(old_dir):
            oldfiles = os.listdir(old_dir)
            for file in oldfiles:
                # move to new config directory
                shutil.move(old_dir + '/' + file, self.dir + '/' + file)

    def latest_release(self, widget):
        '''What is the latest pytomtom release?'''

        try:
            url = 'http://tomonweb.2kool4u.net/pytomtom/LATEST'
            request = urllib2.Request(url, None)
            url_file = urllib2.urlopen(request)
            temp_file = tempfile.NamedTemporaryFile()
            temp_file.write(url_file.read())
            temp_file.flush()
            url_file.close()
            with open(temp_file.name, 'rb') as latest:
                line = latest.readline()
                line = line[:-1]
                latest.close()
            if VER == line:
                msg = _('No need to update. You use the latest stable release.')
                self.popup(msg)
            else:
                msg = _('You can update. The latest stable release is ') + line
                self.popup(msg)
        except:

            msg = _('Impossible to fetch data')
            self.popup(msg)

    def web_connect(self, widget):
        '''open pytomtom homepage in browser'''

        webbrowser.open(WEB_URL)
        return True

    def usage(self):
        '''Fonction d'affichage de l'utilisation des options'''

        # Utilisation de sysr.argv[ 0 ] afin d'avoir toujours le bon nom de l'executable
        print ''
        print 'usage: ' + 'python ' + os.path.basename(sys.argv[0]) \
            + ' [option]'
        print ''
        print '    -h, --help                                 ' \
            + 'This online help'
        print '    -V, --version                              ' \
            + 'Print the name and version of this software'
        print '    -d, --debug         niv                    ' \
            + 'Debugging level, from 0 to 9'
        print '    -l, --log-file      file-to-log            ' \
            + 'Name of traces log file'
        print '    -x, --overwrite-log                        ' \
            + 'Overwrite log file (default is append)'
        print '        --no-exec                              ' \
            + 'Show commands to be executed but do not execute them'
        print '        --print-time-passed                    ' \
            + 'Show elapsed time in progress bar'
        print '        --print-time-remind                    ' \
            + 'Show remaining time in progress bar'
        print '        --print-time-tot                       ' \
            + 'Show total estimated time in progress bar'
        print '    -n, --no-gui                               ' \
            + 'Usage in text mode'
        print '    -s, --save-config                          ' \
            + 'Save configuration file'
        print '    -g, --do-gpsfix                            ' \
            + 'Start update of GPSQuickFix'
        print '    -b, --do-backup                            ' \
            + 'Start backup operation in file ' + self.dir \
            + '/sv-[date-du-jour]-[model].tar[.gz|.bz] ' \
            + '\n                                               or provided with -f'
        print '    -r, --do-restore                           ' \
            + 'Start restore operation from file ' + self.dir \
            + '/sv-[date-du-jour]-[model].tar[.gz|.bz]' \
            + '\n                                               or provided with -f'
        print '    -f, --file          file-to-save           ' \
            + 'Path of backup/restore file'
        print '    -p, --ptmount       dir                    ' \
            + 'Mounting point of the TomTom'
        print '    -m, --model         model                  ' \
            + 'TomTom model, in the list:'
        # Liste des modeles
        for model in self.models:
            print "                                                     '" \
                + model + "'"

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de recuperation des options
    def get_opts(self):

        # initialisation des variables
        mount = False
        model = False
        debug = False
        err = False
        log_file = None

        # On teste la recuperation des arguments
        try:
            # getopt.getopt decoupe la ligne (l'ensemble des arguments : sys.argv[1:]) en deux variables, les options et les arguments de la commande
            #        l'ordre des options importe peu pour la technique, cependant, afin de ne pas mettre deux fois la meme lettre, il est plus
            #        simple de respecter l'ordre alphabetique
            (opts, args) = getopt.getopt(sys.argv[1:], 'bd:f:ghl:m:np:rsxV', [
                'do-backup',
                'debug=',
                'file=',
                'do-gpsfix',
                'help',
                'log-file=',
                'model=',
                'no-gui',
                'ptmount=',
                'do-restore',
                'save-config',
                'overwrite-log',
                'version',
                'no-exec',
                'print-time-passed',
                'print-time-remind',
                'print-time-tot',
                ])
        except getopt.GetoptError, err:
        # Si le test ne fonctionne pas
            # affichage de l'erreure
            self.debug(0, str(err))  # Affichera quelque chose comme "option -a not recognized"
            # Affichage de l'utilisation des options
            self.usage()
            sys.exit(2)

        # Pour chaque option et ses arguments de la liste des options
        for (opt, argument) in opts:
            if opt in ('-b', '--do-backup'):
                self.do_backup = True
                self.debug(5, 'Option Backup')
            elif opt in ('-d', '--debug'):
                # Verification de l'option fournie faite a la fin
                debug = argument
            elif opt in ('-f', '--file'):
                self.file_name = os.path.realpath(argument)
                self.debug(5, 'Option File name: ' + self.file_name)
            elif opt in ('-g', '--do-gpsfix'):
                self.do_gps_fix = True
                self.debug(5, 'Option GPSQuickFix')
            elif opt in ('-h', '--help'):
                self.usage()
                sys.exit()
            elif opt in ('-l', '--log-file'):
                log_file = argument
            elif opt in ('-m', '--model'):
                # Verification du bon choix du modele faite a la fin
                model = argument
            elif opt in ('-n', '--no-gui'):
                self.no_gui = True
                self.debug(5, 'Option Script mode')
            elif opt in ('-p', '--ptmount'):
                # Verification du bon choix du point de montage faite a la fin
                mount = argument
            elif opt in ('-r', '--do-restore'):
                self.do_restore = True
                self.debug(5, 'Option Restore')
            elif opt in ('-s', '--save-config'):
                self.do_save = True
                self.debug(5, 'Option Save configuration')
            elif opt in ('-x', '--overwrite-log'):
                self.overwrite_log = True
                self.debug(5, 'Option Overwrite configuration')
            elif opt in ('-V', '--version'):
                self.print_version()
                sys.exit()
            elif opt in '--no-exec':
                self.no_exec = True
                self.debug(5, 'Option Without execution')
            elif opt in '--print-time-passed':
                self.config_time_passed = True
                self.debug(5, 'Option Print elapsed time in progress bar')
            elif opt in '--print-time-remind':
                self.config_time_remind = True
                self.debug(5, 'Option Print remaining time in progress bar')
            elif opt in '--print-time-tot':
                self.config_time_tot = True
                self.debug(5, 'Option Print total time in progress bar')
            else:
                # Si l'option est mise dans getopt mais n'est pas traite ici
                self.debug(0, 'Option No action')

        # Verifications diverses

        # Changement de fichier de log
        if log_file != None:
            # Choix du mode d'ecriture du fichier de log, par defaut en ajout, si l'option est fournie, on passe en ecrasement
            if self.overwrite_log == True:
                option = 'a'
            else:
                option = 'w'

            # On test l'ecriture dans le nouveau fichier de log
            try:
                # Pour ne pas perdre l'ancien fichier, on ouvre le nouveau dans une nouvelle variable
                log_file = open(log_file, option)
                # Si tout s'est bien passe, on ferme l'ancien fichier (sauf s'il s'agit de stdout)
                if self.log_file != sys.stdout:
                    self.log_file.close()
                # Puis on rattache le nouveau fichier a la variable globale
                self.log_file = log_file
            except:
                # S'il y a une erreur, on affiche un message d'erreur (dans l'ancien fichier de log)
                self.debug(1, 'Impossible to change log file')
        else:
            # S'il n'y a pas de demande de nouveau fichier mais simplement d'excrasement du fichier de log (et qu'il ne s'agit pas
            # de stdout, et re-ouvre (fermeture puis re-ouverture) le fichier de log en ecrasement
            if self.log_file != sys.stdout and self.overwrite_log == True:
                self.log_file.close()
                self.log_file = open(self.log_file_name, 'w')

        # Si les options de sauvegarde et de restauration sont founies en meme temps, il y a erreur
        if self.do_backup and self.do_restore:
            self.debug(0, 'Incompatible options -b and -r')
            # Afin que toutes les options soient testees plutot que de stopper sur la premiere puis la seconde...
            err = True

        # Verification que le modele donne fait partie de la liste des modeles existants
        if not model == False:
            if model in self.models:
                self.model = model
                self.debug(5, 'Selected model: ' + self.model)
            else:
                self.debug(0, 'Invalid model ' + str(model))
                # Afin que toutes les options soient testees plutot que de stopper sur la premiere puis la seconde...
                err = True

        # Verification du point de sauvegarde
        if not mount == False:
            if self.is_pt_mount(mount):
                self.mount = mount
                self.debug(5, 'Selected mounting point: ' + self.mount)
            else:
                self.debug(0, 'Invalid mounting point argument: ' + mount)
                # Afin que toutes les options soient testees plutot que de stopper sur la premiere puis la seconde...
                err = True

        # Verification que le niveau de debug est compris entre 0 et 9
        if not debug == False:
            try:
                if int(debug) >= 0 and int(debug) <= 9:
                    self.log_level = int(debug)
                    self.debug(5, 'Debugging level argument ' + str(int(debug)))
                else:
                    self.debug(1, "Mauvais argument pour l'option de deboggage "
                                + str(int(debug)))
            except:
                self.debug(1, 'Debugging level argument is not an int ' + debug)

        # Si on a une erreur, on arrete le programme
        if err:
            self.usage()
            sys.exit(2)

        return True


    def get_variables(self):

        # Lecture du point de montage (variable PYTOMTOM_PTMOUNT)
        env = os.getenv('PYTOMTOM_PTMOUNT', False)
        if not env == False:
            self.mount = str(env)
            self.debug(5, 'Selected mounting point: ' + str(env))

        # Lecture du modele PYTOMTOM_MODELE
        env = os.getenv('PYTOMTOM_MODELE', False)
        if not env == False:
            self.model = str(env)
            self.debug(5, 'Selected model: ' + str(env))

        # Lecture de l'affichage de la barre de progression
        env = os.getenv('PYTOMTOM_CONFIG_TIME_PASSED', False)
        if not env == False:
            if env == 'False':
                self.config_time_passed = False
            elif env == 'True':
                self.config_time_passed = True
            self.debug(5, 'Elapsed time: ' + str(env))

        # Lecture de l'affichage de la barre de progression
        env = os.getenv('PYTOMTOM_CONFIG_TIME_REMIND', False)
        if not env == False:
            if env == 'False':
                self.config_time_remind = False
            elif env == 'True':
                self.config_time_remind = True
            self.debug(5, 'Remaining time: ' + str(env))

        # Lecture de l'affichage de la barre de progression
        env = os.getenv('PYTOMTOM_CONFIG_TIME_TOT', False)
        if not env == False:
            if env == 'False':
                self.config_time_tot = False
            elif env == 'True':
                self.config_time_tot = True
            self.debug(5, 'Total time: ' + str(env))

        # Afin de valider le mode graphique, on verifie la variable d'environnement DISPLAY
        env = os.getenv('DISPLAY', False)
        if env == False or env == '':
            self.no_gui = True
            self.debug(5, 'Option Script mode')

        return True


    def get_config(self):

        # La lecture du fichier de configuration, puis des options et enfin des variables d'environnement
        # permet de definir l'ordre de preference des donnees si les donnees sont fournies sous differentes formes

        # Verification de l'existence du repertoire de configuration
        if not os.path.exists(self.dir):
            # Creation du repertoire si inexistant
            os.mkdir(self.dir)
            # Verification apres creation afin de valider le systeme
            if not os.path.exists(self.dir):
                self.debug(0, 'Impossible to create configuration file '
                           + self.dir)
                sys.exit(2)
        else:
            # Verification que le dossier de configuration en est bien un
            # TODO : verification en cas de lien vers un dossier plutot qu'un dossier
            if os.path.isdir(self.dir):
                # Verification de l'existence du fichier de configuration
                if os.path.exists(self.dir + '/' + self.config_file):
                    # Ouverture du fichier de configuration en lecture
                    with open(self.dir + '/' + self.config_file, 'rb') as \
                        config:
                        # Lecture des lignes
                        line = config.readline()
                        while line:
                            # suppression des \n de fin de ligne
                            line = line[:-1]
                            # Le fichier se presente sous la forme nom=valeur, on decoupe selon le =
                            line = line.split('=')
                            # Suppression des espaces inutiles en debut et fin de mot
                            name = line[0].strip()
                            # On traite en deux cas, soit le parametre est un string, soit un bouleen
                            if name in ('ptMount', 'model'):
                                # setattr permet d'associer la valeur a l'attribut fourni par son nom au format str
                                # On supprime naturellement les espaces inutiles en debut et fin de mot
                                setattr(self, name, line[1].strip())
                            elif name in ('configTimePassed', 'configTimeRemind'
                                    , 'configTimeTot'):
                            #      deuxieme cas, s'il s'agit d'un bouleen
                                if line[1].strip() == 'True':
                                    setattr(self, name, True)
                                else:
                                    setattr(self, name, False)

                            # lecture de la prochaine ligne
                            line = config.readline()
                    # Fermeture du fichier de configuration
                    config.close()
            else:
                self.debug(0, 'Configuration path is not a directory '
                           + self.dir)
                sys.exit(2)

        # Lecture de la carte utilisee

        # si carminat TODO mount loopdir
        if self.model == 'Carminat':
            if not self.mount == False:
                desktop_environment = 'generic'
                superman = ''
                if os.environ.get('KDE_FULL_SESSION') == 'true':
                    desktop_environment = 'kde'
                    superman = 'kdesu'
                elif os.environ.get('GNOME_DESKTOP_SESSION_ID'):
                    desktop_environment = 'gnome'
                    superman = 'gksudo'

                # cmd = ( "cp '" + self.mount + "/loopdir/ext3_loopback' /tmp && mkdir /tmp/vfs && gksudo 'mount -w /tmp/ext3_loopback /tmp/vfs -t ext3 -o loop'" )
                cmd = "cp '" + self.mount \
                    + "/loopdir/ext3_loopback' /tmp && mkdir /tmp/vfs && " \
                    + superman \
                    + " 'mount -w /tmp/ext3_loopback /tmp/vfs -t ext3 -o loop'"
                print desktop_environment
                print cmd
                p = subprocess.Popen(cmd, shell=True)
                p.wait()
                # TODO methode universelle ou monter un systeme sans etre root, mais la je reve...

                file_ttgobif = os.path.join('/tmp/vfs', 'CurrentMap.dat')
        else:
            self.mount = str(self.mount)
            file_ttgobif = os.path.join(self.mount, 'CurrentMap.dat')  # -->  /media/cle usb 4g/ttgo.bif [OK]

        print str(file_ttgobif)

        if os.path.exists(str(file_ttgobif)):
            with open(file_ttgobif, 'rb') as ttgobif:
                line = ttgobif.readline()
                line = line[:-2]
                line = line.split('/')
                self.current_map = str(line[-1])
                # print self.CurrentMap
            ttgobif.close()

        # Lecture des options
        self.get_opts()
        # Lecture des variables d'environnement
        self.get_variables()

        # Si le point de montage ou le modele n'est pas defini, il faut le definir -> passage sur la fenetre de gestion des options
        #       de meme si le point de montage n'est pas valide
        if self.mount == False or self.is_pt_mount(self.mount) == False \
            or self.model == False:
            self.box_init = 0
            # self.Popup( _( "Connect your device and restart " ) + App )

        # Validation des possibilites de l'application (verification des dependances externes)
        # Lancement de la commande which cabextract qui precise l'emplacement de cabextract, renvoi 0 si trouve, 1 sinon
        p = subprocess.Popen('which cabextract > /dev/null', shell=True)
        if p.wait() != 0:
            self.debug(1, 'cabextract is not installed')
            self.could_gps_fix = False

        # Lancement de la commande which tar qui precise l'emplacement de cabextract, renvoi 0 si trouve, 1 sinon
        p = subprocess.Popen('which tar > /dev/null', shell=True)
        if p.wait() != 0:
            self.debug(1, 'tar is not installed')
            self.could_backup = False

        # Affichage des informations de deboggage
        self.debug(1, 'Application: ' + APP + ' - Version: ' + VER)
        self.debug(1, 'Mounting point used: ' + str(self.mount))
        self.debug(1, 'Model used: ' + str(self.model))
        self.debug(1, 'Curent map: ' + str(self.current_map))

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de mise a jour et d'enregistrement des options par le formulaire
    def on_update(self, entry):

        # Recuperation des differents parametres du formulaire
        model = self.modele_combo.get_model()
        index = self.modele_combo.get_active()
        self.model = str(model[index][0])
        # Pas de verification du modele puisque le choix s'effectue a partir d'une liste fournie par l'application, aucun risque d'erreur

        mount = self.pt_combo.get_model()
        index = self.pt_combo.get_active()
        if self.is_pt_mount(str(mount[index][0])):
            self.mount = str(mount[index][0])

        # Enregistrment des options
        self.put_config()
        self.popup(_('Reload ') + APP + _(' to use this settings.'))

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de sauvegarde de la configuration
    def put_config(self):

        # Verification des donnees a sauvegarder
        if not (self.mount and self.model):
            self.debug(0, 'Cannot write data: ' + "mounting point = '"
                       + str(self.mount) + "' - model = '" + str(self.model)
                       + "'")
            sys.exit(2)

        # Sauvegarde des donnees dans le fichier de configuration
        try:
            config_file = open(self.dir + '/' + self.config_file, 'wb')
            # L'enregistrement des options s'effectue sous le forme nom=valeur
            # getattr permet de recuperr la valeur de l'attribut fourni par son nom au format str
            for option in ('ptMount', 'model', 'configTimePassed',
                           'configTimeRemind', 'configTimeTot'):
                config_file.write(option + '=' + str(getattr(self, option))
                                  + '\n')
        finally:
            # Fermeture du fichier, qu'il y ait une erreur ou non
            config_file.close()

        # Affichage des informations de deboggage
        self.debug(1, 'TomTom: ' + str(self.model) + ' ::saved::')
        self.debug(1, 'Mounting point: ' + str(self.mount) + ' ::saved::')

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de recherche des points de montage disponibles
    def get_pt_mounts(self):

        # Mise a zero de la liste
        self.pt_mounts = []
        # Recuperation de la liste des points de montage de type vfat, avec leur taille
        pt_mounts = self.get_pt_with_size('vfat')
        # Pour chaque point de montage
        for (pt_mount_size, mount) in pt_mounts:
            if pt_mount_size == -1:
                self.debug(5, 'No mounting point')  # 5
                return True

            # Validation du point de montage
            if self.is_pt_mount(mount):
                self.pt_mounts.append([pt_mount_size, mount])

        # Affichage des informations de deboggage
        self.debug(5, 'List of mounting points ' + str(self.pt_mounts))  # 5

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de validation du point de montage
    def is_pt_mount(self, mount_point):

        # Si le point de montage n'est pas fourni ou est faux
        if mount_point == False:
            return False

        # Verification de l'existence du fichier tomtom.ico pour valider qu'il s'agit bien d'un point de montage d'un tomtom
        self.debug(6, 'Testing mounting point ' + mount_point)
        if os.path.exists(mount_point + self.ttgo):
            self.debug(5, 'Valid mounting point: ' + mount_point)
            self.gps_status = 'connected'
            # print "test : ok : tomtom"
            return True

        # Dans tous les autres cas, le point de montage n'est pas valide
        # print "test : ERROR : not a tomtom"
        return False

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction demontage
    def umount(self, mount_point):
        cmd = "umount '" + self.mount + "'"
        p = subprocess.Popen(cmd, shell=True)
        p.wait()
        # self.btnUnmount.set_sensitive( False )
        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction GPSQUICKFIX, mise a jour des donnees de l'emplacement des satellites (a effectuer une fois par semaine)
    def gps_quick_fix(self, widget):
        print 'starting GpsQuickFix...'

        # Si cabextract n'existe pas, on ne fait rien
        if self.could_gps_fix == False:
            return False

        # Verification du point de montage
        if not self.is_pt_mount(self.mount):
            self.debug(1, 'Invalid mounting point: ' + self.mount)
            return False

        # Aucune verification du modele car il provient d'une liste pre-definie

        # Definition du dossier de destination
        dir = str(self.mount + self.dest)

        # Verification de l'existence du du dossier ephem
        self.debug(6, 'Testing ephem directory ' + dir)
        if os.path.exists(dir):
            self.debug(5, 'Valid directory: ' + dir)
        else:
            self.debug(5, 'Creating ephem directory')
            # on cree le repertoire ephem si il n'existe pas
            cmd = 'mkdir ' + dir
            p = subprocess.Popen(cmd, shell=True)
            p.wait()

        if self.model in self.si_rfstar_iii:  # si le tomtom possede un chipset SiRFStarIII
            url = \
                'http://home.tomtom.com/download/Ephemeris.cab?type=ephemeris&amp;eeProvider=SiRFStarIII&amp;devicecode=2'
            self.debug(6, 'chipset SiRFStarIII : ' + url)
        else:
              # sinon (si le tomtom possede un chipset globalLocate)
            url = \
                'http://home.tomtom.com/download/Ephemeris.cab?type=ephemeris&amp;eeProvider=globalLocate&amp;devicecode=1'
            self.debug(6, 'chipset globalLocate : ' + url)

        # Definition d'une requete
        request = urllib2.Request(url, None)
        # Ouverture de la requete
        try:
            # Si l'on veut l'execution, on lance la recuperation de l'url
            if self.no_exec == False:
                url_file = urllib2.urlopen(request)
        except:
            self.debug(1, 'Impossible to fetch URL: ' + url)
            return False

        # Autant de try imbrique afin de fournir des messages justes, et de supprimer correctement les fichiers et dossiers temporaires
        # Le cab est recupere dans un fichier temporaire, puis extrait dans un dossier temporaire
        try:
            # Creation d'un repertoire temporaire pour extraire le cab telecharge
            temp_dir_name = tempfile.mkdtemp()
            self.debug(5, 'Creating temporary directory: ' + temp_dir_name)
            try:
                # Creation d'un fichier temporaire pour le telechargement du cab
                temp_file = tempfile.NamedTemporaryFile()
                self.debug(5, 'Creating temporary file: ' + temp_file.name)
                try:
                    self.debug(5, 'Fetching data: ' + url)
                    # Si l'on veut une execution, on telecharge le cab
                    if self.no_exec == False:
                        temp_file.write(url_file.read())
                        temp_file.flush()
                        url_file.close()
                    try:
                        # Extraction du cab seulement si l'on veut l'execution, sinon un simple affichage de ce que l'on aurait fait
                        if self.no_exec == False:
                            cmd = 'cabextract -d ' + temp_dir_name + ' ' \
                                + temp_file.name + '; touch ' + temp_dir_name \
                                + '/*'
                        else:
                            cmd = 'echo cabextract -d ' + temp_dir_name + ' ' \
                                + temp_file.name + '; echo touch ' \
                                + temp_dir_name + '/*'
                        self.debug(5, 'Launching command ' + cmd)
                        # Lancement du processus
                        p = subprocess.Popen(cmd, shell=True)
                        p.wait()
                        try:
                            # Deplacement de tous les fichiers du cab vers la destination
                            #     Ceci evite de faire une difference entre les deux modeles de chipset
                            files = os.listdir(temp_dir_name)
                            for file in files:
                                self.debug(5,
                                        'Moving file to final destination: '
                                        + temp_dir_name + '/' + file + ' -> '
                                        + self.mount + self.dest + '/'
                                        + file)
                                # ATTENTION : si le fichier destination est un repertoire, et que le fichier existe
                                #             shutil.move fait une erreur, il faut donc preciser le fichier de destination
                                #             pour l'ecraser, et non simplement le repertoire de destination
                                shutil.move(temp_dir_name + '/' + file,
                                        self.mount + self.dest + '/' + file)
                        except:
                            self.debug(0, 'Impossible to move data')
                    except:
                        self.debug(0, 'Impossible to extract data')
                except:
                    self.debug(0, 'Impossible to fetch data')
            except:
                self.debug(0, 'Impossible to create temporary file')
            finally:
                # Fermeture propre du fichier temporaire (avec sa suppression) dans tous les cas (meme si un probleme survient)
                temp_file.close()
        except:
            self.debug(0, 'Impossible to create temporary directory')
        finally:
            # Suppression du dossier temporaire dans toça c'est la dernière, supprime tout le reste...us les cas (meme si un probleme survient)
            shutil.rmtree(temp_dir_name)

        # Affichage de la fin de l'execution, en popup si l'on est pas en mode script
        if self.no_gui == False:
            self.popup(_('GPSQuickFix completed'))
        self.debug(1, 'GPSQuickFix completed')

        return True

    def get_pt_with_size(self, type=None, mount=None):
        ''' Retrieve mounted partitions name and size.

            limite par un type de systeme,
            ou/et un point de montage

        '''

        # Ecriture de la commande, df pour lister,
        #     -t pour specifier le type selectionne,
        #     -T pour afficher le type du systeme de fichier
        #     -l pour lister uniquement les systemes de fichiers locaux
        #     -P pour avoir le format posix
        #     --output-delimiter pour s'assurer le delimiteur final avant traitement (commande split)
        #     -B 1 pour utiliser une taille de 1 octet pour l'affichage
        #     Si la commande ne liste aucun systeme de fichier, un message d'erreur est fourni, on re-dirige donc les erreurs sur /dev/null
        #     La commande df affiche une entete inutile, d'ou le tail -n +2 (on commence a la deuxieme ligne)
        #     Afin de pouvoir decouper facilement la ligne, on remplace les ensembles d'espace par un unique espace - commande tr -s
        #     Afin de ne retenir que les donnees utiles, on recupere les champs 4 et 7 - commande cut
        cmd = 'df -B 1 -TlP'
        if not type == None:
            cmd += 't ' + type + ' '
        if not mount == None:
            cmd += ' "' + mount + '"'
        # cmd += " 2> /dev/null | tail -n +2 | tr -s ' ' | cut -d ' ' -f 4,7 --output-delimiter=,"
        cmd += " 2> /dev/null | tail -n +2 | tr -s ' ' | cut -d ' ' -f 4,7-"

        # Lancement de la commande, avec recuperation du stdout dans le processus actuel
        self.debug(5, 'launching command: ' + cmd)  # 5
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        res = []
        # Lecture du resultat
        for line in p.stdout:
            # Suppression du \n de la ligne
            line = line[:-1]
            line = line.split(' ', 1)
            self.debug(5, 'Command result: ' + str(int(line[0])) + ' -> '
                       + line[-1])  # 5
            # res.append( [ int( line[ 0 ] ), line[ 1 ] ] )
            res.append([int(line[0]), line[-1]])
        p.wait()

        if res == []:
            # le resultat de la fonction est une liste de liste contenant la taille et le nom du point de montage
            return [[-1, None]]

        # Renvoi des donnees collectees
        return res

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de recherche d'un enfant de self.window, le nom fourni sous la forme nom_frame.nom_box.... 7
    def search_obj(self, name):

        # TODO : existe-t-il deja une fonction plus rapide ?
        # Decoupage du nom par le separateur "."
        name = name.split('.')

        # On commence au niveau self.window
        obj_parent = self.window
        self.debug(7, 'Searched object: ' + str(name))

        # Pour tous les niveaux du nom fourni
        for i in range(0, len(name) - 1, 1):
            self.debug(7, 'Scanning level: ' + str(i))

            # Enfant non trouve
            find = False

            # Pour chaque enfant
            for obj_child in obj_parent:
                self.debug(7, '     Object scanned: ' + obj_child.get_name())
                # Si le nom correspond
                if obj_child.get_name() == name[i]:
                    self.debug(7, 'Object found')
                    # Le parent devient l'enfant pour continuer la recherche au niveau suivant
                    obj_parent = obj_child
                    # On a bien trouve l'enfant
                    find = True
                    break

            # Si l'enfant n'est pas trouve a ce niveau, on arrete tout
            if find == False:
                return None

        # retour de l'enfant, comme le parent est devenu l'enfant, il suffit de retourner le parent (on est sur qu'il est defini)
        return obj_parent

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction de remplacement image de demarrage avec toutes les verifications utiles
    def change_start_img(self, widget):

        # TODO : mettre en place la reconnaissance des noms des images a remplacer
        if os.path.exists(self.mount + '/splash.bmp'):
            return True  # ecran normal n
        else:
            # subprocess.call( [ "convert image.jpg -resize 320x240 -background black -gravity center -extent 320x240 splash.bmp" ], shell = True )
            if os.path.exists(self.mount + '/splashw.bmp'):  # elif ?? non
                return True  # ecran widescreen w

                # subprocess.call( [ "convert image.jpg -resize 480x272 -background black -gravity center -extent 480x272 splash.bmp" ], shell = True )

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de creation d'un nom de fichier de sauvegarde
    def get_new_file_name(self, uniq=False):

        # si l'option uniq est fournie, on ajoute un nombre aleatoire
        if uniq == False:
            return self.dir_backup + '/sv-' + str(date.today()) + '-' \
                + self.model + '.tar'
        else:
            return self.dir_backup + '/sv' + str(random.randint(1, 50)) + '-' \
                + str(date.today()) + '-' + self.model + '.tar'

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction de lancement du Backup et de la restauration avec toutes les verifications utiles
    def backup_restore_gps(self, widget, type):

        # Verification du point de montage
        if not self.is_pt_mount(self.mount):
            self.debug(1, 'Invalid mounting point: ' + self.mount)
            return False

        # Recuperation du nom du fichier de sauvegarde
        files = self.save_file_combo.get_model()
        index = self.save_file_combo.get_active()
        if files[index][0] == '':
            self.debug(2, 'Invalid file selected for ' + _(type))
            return False
        self.file_name = files[index][0]
        self.debug(1, 'File for ' + _(type) + ': ' + self.file_name)

        if type == 'restore':
            if not os.path.exists(self.file_name):
                self.debug(1, 'Backup file not found')
                return False

        if self.no_gui == False:
            obj = \
                self.search_obj('notebook.frameSaveRestore.boxSaveRestore.btnSave'
                                )
            if obj != None:
                obj.set_sensitive(False)
            obj = \
                self.search_obj('notebook.frameSaveRestore.boxSaveRestore.btnRestore'
                                )
            if obj != None:
                obj.set_sensitive(False)

        # Verification de l'espace disponible par rapport a l'espace initial,

        # Recuperation d'un tableau de toutes les partitions de type
        #     les donnees sont sur la ligne 0 puisque nous n'avons qu'une seule ligne
        self.pt_mount_size = self.get_pt_with_size('vfat', self.mount)
        # Recuperation du nom de la partition impactee,
        #     en effet, si l'on fournit /boot, on retrouve / car /boot n'est pas monte et fait partie du systeme /
        self.mount = self.pt_mount_size[0][1]
        # Recuperation de la taille de la partition
        self.pt_mount_size = self.pt_mount_size[0][0]

        if self.pt_mount_size == -1:
            self.debug(1, 'Impossible to compute filesystem size')
            return False
        self.debug(5, 'Mounting point size: ' + self.mount + ' -> '
                   + str(self.pt_mount_size))

        # Recuperation de la taille de la partition hote du fichier de sauvegarde
        size = self.get_pt_with_size(None,
                                     os.path.dirname(os.path.realpath(self.file_name)))
        size = size[0][0]
        self.debug(5, 'Backup partition size: ' + str(size))

        # Attention, si la taille de la partition de la sauvegarde est trop petite
        if self.pt_mount_size > size:
            self.debug(1, 'Insufficient disk space: ' + str(size) + ' for '
                       + str(self.pt_mount_size))
            return False

        # ajout d'affichage supplementaire de la commande tar si le debug est suffisament important
        option = ''
        if self.log_level >= 4:
            option += 'v'

        # Choix de la commande s'il faut faire un backup ou une restauration, choix du texte a afficher dans la barre de progression
        if type == 'backup':
            option += 'c'
            text = _('Creation')
        elif type == 'restore':
            option += 'x'
            text = _('Restoration')

        # Si le processus precedent n'a pas ete lance ou n'est pas fini (ex : poll = None), on attend
        if self.proc_backup == None or self.proc_backup.poll() != None:
            # -u pour creer ou mettre a jour une archive
            # -f pour preciser le nom de l'archive plutot que sur le stdout
            # Execution de la commande seuleument si l'on veut, sinon affichage de ce que l'on aurait fait
            if self.no_exec == False:
                cmd = "cd '" + self.mount + "'; tar -" + option + 'f "' \
                    + self.file_name + '" .'
            else:
                cmd = "cd '" + self.mount + "'; echo tar -" + option + 'f "' \
                    + self.file_name + '" .'
            self.debug(5, 'Launching command: ' + cmd)
            self.proc_backup = subprocess.Popen(cmd, shell=True)

            # verification de la fin du processus
            if self.proc_backup.poll() != None:
                # Si l'on est pas en mode script, on affiche un popup de fin de processus
                if self.no_gui == False:
                    self.popup(text + _(' completed'))
                self.debug(5, text + ' completed')

            # Lancement de la barre de progression
            self.debug(5, 'Launching the test of ' + text
                       + ' of archive each second')
            # Supression du tempo avant sa re-utilisation
            if self.tempo != None:
                gobject.source_remove(self.tempo)
            # Saut de ligne pour etre sur d'afficher correctement la barre de progression
            sys.stdout.write('\n')
            sys.stdout.flush()
            # Creation d'un timeout toutes les n ms, lancement de la fonction self.Progress avec ces parametres
            self.tempo = gobject.timeout_add(
                self.tempo_delay,
                self.progress,
                100,
                100,
                text + ' of archive',
                self._backup_restore_gpsend,
                text,
                )

            return False

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de calcul et de mise en forme des temps estimes restant, total et du temps passe
    def get_time_delay(self, percent):

        # Calcul du temps passe (en secondes) depuis le lancement de la sauvegarde
        seconds_pass = gobject.get_current_time() - self.tempo_start_time
        # Calcul du temps estime total (en secondes) - en supposant que le temps passe est lineaire par rapport au travail effectue
        #      pour le tar, ce n'est pas le cas, rapide jusqu'a 11%, puis apparement lineaire, tres proche a partir de 40% - 37mn pour 1,6Go
        #      pour le bzip2, on l'est quasiment, à 2% on est tres proche - 22mn pour 1,6Go compresse en 1,5Go soit 98% - inutile !!!
        #      pour le bunzip2, il faut 8mn
        seconds_tot = seconds_pass / percent
        # Calcul du temps estime restant (en secondes)
        seconds_remind = seconds_tot - seconds_pass

        # Calcul du nombre d'heures passe (pour l'affichage)
        hours_pass = str(int(seconds_pass / 3600))
        # Calcul du nombre de minutes estimees au total, sans les heures calculees auparavant (pour l'affichage)
        minutes_pass = str(int(seconds_pass / 60 % 60))
        # Calcul du nombre de secondes estimees au total, sans les heures et les minutes calculees auparavant (pour l'affichage)
        seconds_pass = str(int(seconds_pass % 60))

        # Calcul du nombre d'heures estimees au total (pour l'affichage)
        hours_tot = str(int(seconds_tot / 3600))
        # Calcul du nombre de minutes estimees au total, sans les heures calculees auparavant (pour l'affichage)
        minutes_tot = str(int(seconds_tot / 60 % 60))
        # Calcul du nombre de secondes estimees au total, sans les heures et les minutes calculees auparavant (pour l'affichage)
        seconds_tot = str(int(seconds_tot % 60))

        # Calcul du nombre d'heures estimees restantes (pour l'affichage)
        hours_remind = str(int(seconds_remind / 3600))
        # Calcul du nombre de minutes estimees restantes, sans les heures calculees auparavant (pour l'affichage)
        minutes_remind = str(int(seconds_remind / 60 % 60))
        # Calcul du nombre de secondes estimees restantes, sans les heures et les minutes calculees auparavant (pour l'affichage)
        seconds_remind = str(int(seconds_remind % 60))

        # Mise en place de l'affichage du temps a afficher, en fonction des options fournies
        time_to_print = ''
        if self.config_time_passed == True:
            time_to_print += hours_pass + ':' + minutes_pass + ':' \
                + seconds_pass + ' -> '
        if self.config_time_remind == True:
            time_to_print += hours_remind + ':' + minutes_remind + ':' \
                + seconds_remind
        if self.config_time_tot == True:
            time_to_print += ' / ' + hours_tot + ':' + minutes_tot + ':' \
                + seconds_tot

        # Renvoi du texte a afficher
        return time_to_print

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction de validation du processus apres sa fin
    def _backup_restore_gpsend(self, type):

        # Test de la valeur retournee pour valider ou non la tache finie
        if self.proc_backup.poll() != 0:
            type += _(' failed')
        else:
            type += _(' completed')

        self.debug(1, type + ': ' + str(self.proc_backup.poll()))

        # Si l'on est pas en mode script, on re-active les boutons de lancement des taches
        if self.no_gui == False:
            # Recherche du bouton btnSave
            obj = \
                self.search_obj('notebook.frameSaveRestore.boxSaveRestore.btnSave'
                                )
            if obj != None:
                # Activation du bouton (de-sactive auparavant)
                obj.set_sensitive(True)
            obj = \
                self.search_obj('notebook.frameSaveRestore.boxSaveRestore.btnRestore'
                                )
            if obj != None:
                obj.set_sensitive(True)
            # Affichage du resultat par un popup
            self.popup(type)

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction d'affichage de la barre de progression
    def progress(
        self,
        percent_min,
        percent_max,
        text,
        funct_end,
        param_end,
        ):

        # TODO : possibilite de mettre en pause
        # La premiere fois que la fonction est lancee, l'application a deja ete lancee il y a self.tempoDelay secondes
        if self.tempo_start_time == None:
            self.tempo_start_time = gobject.get_current_time() \
                - self.tempo_delay

        # Si le processus est fini
        if self.proc_backup.poll() != None:

            # Recuperation du temps a afficher, etant arrive a 1, soit 100% (le processus est fini)
            time_to_print = self.get_time_delay(1)
            # Creation du texte de la barre de progression
            text = '%s : 100%% - %s' % (text, time_to_print)
            # Taille de la barre en mode texte
            try:
                bar_size = struct.unpack('HH', fcntl.ioctl(sys.stdout.fileno(),
                        termios.TIOCGWINSZ, struct.pack('HH', 0, 0)))[1] \
                    - len(text) - 5
            except:
                bar_size = 120

            # Affichage de la barre de progression en mode texte
            out = '\r [%s] %s\n' % ('=' * bar_size, text)
            sys.stdout.write(out)
            sys.stdout.flush()

            # Si l'on est en mode graphique
            if self.no_gui == False:
                # Centrage du texte sur une taille de self.progressionBarSize (permettant d'avoir une barre de progression toujours a la meme taille
                text_to_print = text.center(self.progression_bar_size)
                # Affichage de la barre de progression (la valeur doit etre inferieure ou egale a 1
                self.progression_bar.set_fraction(1)
                # Affichage du texte sur la barre de progression
                self.progression_bar.set_text(text_to_print)

            # Lancement de la fonction de validation du processus
            funct_end(param_end)

            # Suppression du minuteur et de la date de debut du processus
            gobject.source_remove(self.tempo)
            self.tempo = None
            self.tempo_start_time = None

            # Si on a deja voulu quitter, on quitte a la fin du processus
            if self.quit == True:
                self.debug(5, 'Exiting on request')
                self.delete(None)

            # Pour arreter le minuteur, il faut renvoyer False
            return False

        # Le processus n'est pas fini, il faut calculer et afficher la barre de progression
        # Initialisation du type de la nouvelle valeur, un nombre flottant a 2 valeurs apres la virgule
        new_val = round(float(0.01), 2)
        # Recuperation de la taille du fichier de destination
        new_size = os.path.getsize(self.file_name)
        self.debug(7, 'File size: ' + self.file_name + ' -> ' + str(new_size)
                   + ' / ' + str(self.pt_mount_size))

        # On estime que la taille du fichier finale sera percentMin, mais qu'au maximum le fichier aura une taille de percentMax
        # On calcul donc le pourcentage estime entre ces deux valeurs, avec des sauts de 10 pourcent
        for percent in range(percent_min, percent_max + 10, 10):
            # Si la taille du fichier est inferieur au pourcentage de la taille du fichier original, on calcule la nouvelle
            # valeur de la barre de progression comprise entre 0,00 et 1
            if new_size <= self.pt_mount_size * percent / 100:
                self.debug(7, '<' + str(percent))
                new_val = round(float(new_size / float(self.pt_mount_size
                                * percent / 100)), 2)
                break
            elif percent > percent_max:
            # Si toutefois on depasse le pourcentage maximum, la valeur restera a 1 (soit 100%)
                new_val = 1

        # Au depart, pas d'idees sur le temps restant, il vient au fur et a mesure
        time_to_print = ''
        if new_val >= 0.01:
            # Recuperation de l'affichage du temps estime restant, total et du temps passe
            time_to_print = self.get_time_delay(new_val)

        # Remise sous la forme 100%, soit un entier compris entre 0 et 100
        new_val = int(100 * new_val)
        # Presentation avec le texte, le pourcentage et le temps a afficher
        text = '%s : %3d %% - %8s' % (text, new_val, time_to_print)
        # Taille de la barre en mode texte
        try:
            bar_size = struct.unpack('HH', fcntl.ioctl(sys.stdout.fileno(),
                                     termios.TIOCGWINSZ, struct.pack('HH', 0,
                                     0)))[1] - len(text) - 5
        except:
            bar_size = 120

        if self.no_gui == False:
            # Ajustement de la taille de la progress barre à 120 caracteres avec centrage du texte
            text_to_print = text.center(self.progression_bar_size)
            # Affichage de la barre de progression (la valeur doit etre inferieure a 1)
            self.progression_bar.set_fraction(round(float(new_val) / 100, 2))
            # Affichage du texte sur la barre de progression
            self.progression_bar.set_text(text_to_print)

        # Pour l'affichage en mode texte, calcul de la valeur par rapport a la taille de la barre en mode texte
        new_val = new_val * bar_size / 100
        # Affichage de la barre de progression
        out = '\r [%s%s] %s' % ('=' * new_val, ' ' * (bar_size - new_val), text)
        sys.stdout.write(out)
        sys.stdout.flush()

        # Pour continuer la barre de progression, il faut renvoyer la valeur True
        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction pour quitter l'application
    def delete(self, widget, event=None):

        # Afin de ne pas quitter sauvagement les processus en cours de sauvegarde ou de restauration, on ne quitte que si
        #     le processus est termine, il faut donc revenir, d'ou l'enregistrement de self.quit pour revenir a la fin du processus
        self.quit = True

        # Supression de la mise a jour automatique du combo de la liste des points de montage
        if self.tempo_combo != None:
            gobject.source_remove(self.tempo_combo)

        # On ne quitte que si le sous-processus est fini
        if self.tempo != None:
            self.debug(1, 'Waiting for end of child process')
            return False

        # Fermeture du fichier de log, si ce n'est pas stdout
        if self.log_file != sys.stdout:
            self.log_file.close()

        # Si l'on est pas en mode script, fermeture de gtk
        if not self.no_gui:
            gtk.main_quit()
        else:
        # Sinon, sortie par le mode sys
            sys.exit(0)

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de creation et d'affichage d'un onglet
    def create_custom_tab(
        self,
        text,
        notebook,
        frame,
        ):

        # On crée une eventbox
        event_box = gtk.EventBox()
        # On crée une boite horizontale
        tab_box = gtk.HBox(False, 2)
        # On crée un label "text" (text donné en attribut)
        tab_label = gtk.Label(text)

        event_box.show()
        tab_label.show()
        # On attache tablabel
        tab_box.pack_start(tab_label, False)

        tab_box.show_all()
        # On ajoute la boite à l'eventbox
        event_box.add(tab_box)

        return event_box

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction d'affichage d'un popup
    def popup(self, text):

        # Creation d'un popup
        dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO,
                                   gtk.BUTTONS_OK, text)
        # Affichage du popup
        dialog.run()
        # Suppression du popup
        dialog.destroy()

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction d'affichage et de mise a jour du combo des points de montage
    def make_combo(self):

        # Recuperation des points de montage potentiels
        self.get_pt_mounts()

        # Creation du combo s'il n'existe pas
        if self.pt_combo == None:
            self.pt_combo = gtk.combo_box_new_text()
            # Affichage d'une ligne vide, afin de forcer le choix s'il n'a pas ete fait auparavant
            self.pt_combo.append_text('')

        # Recuperation des donnees du combo
        combo = self.pt_combo.get_model()

        # --------- Premiere etape, ajout des points de montage inexistants ---------

        # Pour chaque point de montage
        for (pt_mount_size, mount) in self.pt_mounts:
            # Par defaut on a pas trouve
            found = False
            # Pour chaque element du combo (on commence a 1 puisqu'on a un element vide)
            for i in range(1, len(combo), 1):
                # Si l'on trouve le point de montage, on arrete le parcours
                if mount == combo[i][0]:
                    found = True
                    break
            # Si l'on est arrive au bout du combo, on a pas trouve le point de montage
            if found == False:
                # On ajoute le point de montage
                self.pt_combo.append_text(str(mount))
                if mount == self.mount:
                    # Si le point de montage est enregistre, on selectionne ce point de montage dans le combo
                    self.pt_combo.set_active(len(combo) - 1)

        # --------- Deuxieme etape, supression des points de montage n'existant plus ---------
        # Pour chaque element du combo (on commence a 1 puisqu'on a un element vide)
        for i in range(1, len(combo), 1):
            # Par defaut, on a pas trouve l'element
            found = False
            # Pour chaque point de montage
            for (pt_mount_size, mount) in self.pt_mounts:
                # Si on trouve le point de montage
                if mount == combo[i][0]:
                    found = True
            # Si le point de montage n'a pas ete trouve, on le supprime
            if found == False:
                self.pt_combo.remove_text(i)

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de mise a jour de la variable associee a chaque case a cocher pour l'affichage des temps restant, total, passe
    def update_config_time(self, widget):

        # Recuperation du nom de la case a cocher
        name = widget.get_name()
        # Modification de la variable associee (meme nom)
        setattr(self, name, widget.get_active())

        return True

    # ------------------------------------------ DEFINITION DES FONCTIONS D'AFFICHAGE ----------------------------------------
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de creation de la frame des options
    def frame_option(self, notebook):

        # --------------------------------------
        # Onglet OPTIONS
        # --------------------------------------
        frame = gtk.Frame(_('Options'))
        frame.set_border_width(10)
        frame.set_name('frameOptions')
        frame.show()

        # On crée une boite verticale
        tab_box = gtk.HBox(False, 2)
        tab_box.set_name('frameOptions')
        frame.add(tab_box)
        tab_box.show()

        # On crée une boite horizontale
        tab_box_left = gtk.VBox(False, 2)
        tab_box_left.set_size_request(120, -1)
        tab_box.add(tab_box_left)
        tab_box_left.show()
        # On crée une boite horizontale
        tab_box_right = gtk.VBox(False, 2)
        tab_box_right.set_size_request(480, -1)
        tab_box.add(tab_box_right)
        tab_box_right.show()

        # image
        image = gtk.Image()
        image.set_from_file(self.dir_pix + 'options.png')
        tab_box_left.pack_start(image, True, False, 2)

        label = gtk.Label(_('Please indicate the mounting point of your Tomtom:'
                          ))
        label.set_justify(gtk.JUSTIFY_CENTER)
        tab_box_right.pack_start(label, True, False, 2)

        # bouton parcourir
#        p = gtk.Button( _( "Sélectionner le point de montage du TomTom..." ) )
#      tabBox.pack_start( p, True, False, 2 )
#        p.connect( "clicked", self.parcourir_gps )

        # Liste des points de montage possibles
        self.make_combo()
        tab_box_right.pack_start(self.pt_combo, True, False, 0)
        # Lancement de la mise a jour automatiquement toutes les 2 secondes
        self.tempo_combo = gobject.timeout_add(2000, self.make_combo)

        # separator
        hs = gtk.HSeparator()
        tab_box_right.pack_start(hs, False, False, 2)

        # Liste des modeles
        self.modele_combo = gtk.combo_box_new_text()
        i = 0
        for text in self.models:
            self.modele_combo.append_text(str(text))
            if text == self.model:
                self.modele_combo.set_active(i)
            i += 1
        # self.modeleCombo.connect( 'changed', self.OnUpdate )
        tab_box_right.pack_start(self.modele_combo, True, False, 0)

        hs = gtk.HSeparator()
        tab_box_right.pack_start(hs, False, False, 2)

        label = gtk.Label(_('During backup or restore, display:'))
        label.set_justify(gtk.JUSTIFY_CENTER)
        tab_box_right.pack_start(label, True, False, 2)

        # Case a cocher pour l'affichage du temps passe dans la barre de progression
        button = gtk.CheckButton(_('elapsed time'), False)
        button.set_name('configTimePassed')
        button.connect('clicked', self.update_config_time)
        if self.config_time_passed == True:
            button.set_active(True)
        tab_box_right.pack_start(button, True, False, 0)

        # Case a cocher pour l'affichage du temps estime restant dans la barre de progression
        button = gtk.CheckButton(_('remaining time'), False)
        button.set_name('configTimeRemind')
        button.connect('clicked', self.update_config_time)
        if self.config_time_remind == True:
            button.set_active(True)
        tab_box_right.pack_start(button, True, False, 0)

        # Case a cocher pour l'affichage du temps estime total dans la barre de progression
        button = gtk.CheckButton(_('total time'), False)
        button.set_name('configTimeTot')
        button.connect('clicked', self.update_config_time)
        if self.config_time_tot == True:
            button.set_active(True)
        tab_box_right.pack_start(button, True, False, 0)

        # separator
        hs = gtk.HSeparator()
        tab_box_right.pack_start(hs, True, False, 2)

        button = gtk.Button(stock=gtk.STOCK_SAVE)
        tab_box_right.pack_start(button, True, False, 0)

        # Connexion du signal "clicked" du GtkButton
        button.connect('clicked', self.on_update)

        event_box = self.create_custom_tab(_('Options'), notebook, frame)
        notebook.append_page(frame, event_box)

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de creation de la frame du GPSFix
    def frame_gpsquick_fix(self, notebook):

        # --------------------------------------
        # Onglet GPSQuickFix
        # --------------------------------------
        frame = gtk.Frame(_('GPSQuickFix'))
        frame.set_border_width(10)
        frame.set_name('frameGPSQuickFix')
        frame.show()

        # On crée une boite verticale
        tab_box = gtk.HBox(False, 2)
        tab_box.set_name('boxGPSQuickFix')
        frame.add(tab_box)
        tab_box.show()

        # On crée une boite horizontale
        tab_box_left = gtk.VBox(False, 2)
        tab_box_left.set_size_request(120, -1)
        tab_box.add(tab_box_left)
        tab_box_left.show()
        # On crée une boite horizontale
        tab_box_right = gtk.VBox(False, 2)
        tab_box_right.set_size_request(480, -1)
        tab_box.add(tab_box_right)
        tab_box_right.show()

        # image
        image = gtk.Image()
        image.set_from_file(self.dir_pix + 'gpsquickfix.png')
        tab_box_left.pack_start(image, True, False, 2)

        # label
        label = \
            gtk.Label(_('''This update sets the last known positions of the satellites.

It allows your GPS to find its initial position in less than 30 seconds
and to initiate navigation more quickly...

Please ensure that you have properly set your GPS parameters
in the options.'''))
        # On centre le texte
        label.set_justify(gtk.JUSTIFY_CENTER)
        tab_box_right.pack_start(label, True, False, 2)

        # bouton maj quickfix
        if self.could_gps_fix:
            btn_csi = gtk.Button(_('Start GPSQuickfix update'))
            tab_box_right.pack_start(btn_csi, True, False, 2)
            # On connecte le signal "clicked" du bouton a la fonction qui lui correspond
            btn_csi.connect('clicked', self.gps_quick_fix)
        else:
            btn_csi = \
                gtk.Button(_('Cannot start GPSQuickfix update (cabextract is missing)'
                           ))
            btn_csi.set_sensitive(False)
            tab_box_right.pack_start(btn_csi, True, False, 2)
            # On ne connecte à aucune fonction

        event_box = self.create_custom_tab(_('GPSQuickFix'), notebook, frame)
        notebook.append_page(frame, event_box)

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de creation de la frame de lancement du backup et de la restauration
    def frame_backup_restore(self, notebook):

        # ---------------------------------------------------------------------
        # Onglet SAUVEGARDE ET RESTAURATION
        # ---------------------------------------------------------------------

        frame = gtk.Frame(_('Backup and restore'))
        frame.set_border_width(10)
        frame.set_name('frameSaveRestore')
        frame.show()

        # On crée une boite verticale
        tab_box = gtk.HBox(False, 2)
        tab_box.set_name('boxSaveRestore')
        frame.add(tab_box)
        tab_box.show()

        # On crée une boite horizontale
        tab_box_left = gtk.VBox(False, 2)
        tab_box_left.set_size_request(120, -1)
        tab_box.add(tab_box_left)
        tab_box_left.show()
        # On crée une boite horizontale
        tab_box_right = gtk.VBox(False, 2)
        tab_box_right.set_size_request(480, -1)
        tab_box.add(tab_box_right)
        tab_box_right.show()

        # image
        image = gtk.Image()
        image.set_from_file(self.dir_pix + 'saverestore.png')
        tab_box_left.pack_start(image, True, False, 2)

        # Text pour le choix du fichier de sauvegarde
        label = gtk.Label(_('Backup file:'))
        label.set_justify(gtk.JUSTIFY_CENTER)
        tab_box_right.pack_start(label, True, False, 2)

        # TODO : n'afficher que le nom du fichier, pas le chemin complet
        # Liste des fichiers de sauvegarde existant et un nouveau
        self.save_file_combo = gtk.combo_box_new_text()
        # recuperation du nom d'un fichier
        file = self.get_new_file_name()
        # Si le fichier existe, recuperation d'un nom presque certainement inexistant
        if os.path.exists(file):
            file = self.get_new_file_name(True)

        # Creation d'un combo contenant la liste des fichiers de sauvegarde
        # Ajout du nom de fichier nouveau (si l'on veut en creer un nouveau)
        self.save_file_combo.append_text(file)
        # Ajout d'une ligne vide
        self.save_file_combo.append_text('----------------')

        # Si le nom du fichier a ete fourni, ajout du nom du fichier, et selection du fichier dans le combo
        if self.file_name != False:
            self.save_file_combo.append_text(os.path.realpath(self.file_name))
            self.save_file_combo.set_active(2)
        else:
        # Sinon selection du nouveau fichier
            self.save_file_combo.set_active(0)

        # Verification ou creation du dossier backup
        if not os.path.exists(self.dir_backup):
            os.mkdir(self.dir_backup)
        # importation des anciennes sauvegardes (pytomtom =< 0.4)
        # Ouverture de l ancien dossier de sauvegarde
        oldfiles = os.listdir(self.dir)
        for file in oldfiles:
            (f, extension) = os.path.splitext(file)
            if extension == '.tar' and (self.file_name == False
                                        or os.path.realpath(self.dir + '/'
                                        + file)
                                        != os.path.realpath(self.file_name)):
                # on copie les anciennes sauvegardes dans le nouveau rep backup
                shutil.move(self.dir + '/' + file, self.dir_backup + '/' + file)

        # Ajout de tous les anciens fichiers de sauvegarde
        # Ouverture du dossier de sauvegarde
        # files = os.listdir( self.dir )
        files = os.listdir(self.dir_backup)
        # Pour chaque fichier
        for file in files:
            # Recuperation de l'extension du fichier pour savoir s'il s'agit d'une sauvegarde
            (f, extension) = os.path.splitext(file)
            # Ajout du fichier de sauvegarde, s'il s'agit d'une sauvegarde, et qu'il ne s'agit pas du fichier fourni en option
            # if( extension == ".tar" and ( self.fileName == False or os.path.realpath( self.dir + "/" + file ) != os.path.realpath( self.fileName ) ) ):
            if extension == '.tar' and (self.file_name == False
                                        or os.path.realpath(self.dir_backup
                                        + '/' + file)
                                        != os.path.realpath(self.file_name)):
                self.save_file_combo.append_text(self.dir_backup + '/' + file)

        # self.saveFileCombo.set_size_request ( 60, -1 )
        tab_box_right.pack_start(self.save_file_combo, True, False, 0)

        # Mise en place de la barre de progression
        self.progression_bar = gtk.ProgressBar()

        # Affichage du texte dans la barre de progression pour avoir une taille precise de la barre
        text = ''
        self.progression_bar.set_text(text.center(self.progression_bar_size))
        align = gtk.Alignment(0.5, 0.5, 0, 0)
        tab_box_right.pack_start(align, False, False, 10)
        align.show()
        align.add(self.progression_bar)
        self.progression_bar.show()

        # Affichage d'information de la duree
        label = gtk.Label(_('In order to complete these operations ') + APP
                          + _(''' takes time
and consumes disk space.
For information, 25 minutes and 1GB on disk for a One Series 30'''))
        label.set_justify(gtk.JUSTIFY_CENTER)
        tab_box_right.pack_start(label, True, False, 2)

        # separator
        hs = gtk.HSeparator()
        tab_box_right.pack_start(hs, True, False, 2)

        # bouton sauvegarde
        # Si la commande tar n'existe pas, la sauvegarde ne peut etre lancee, l'affichage change et le bouton ne peut
        #     etre clique
        if self.could_backup:
            btn_save = gtk.Button(_('Start backup...'))
            btn_save.props.name = 'btnSave'
            tab_box_right.pack_start(btn_save, True, False, 2)
            # On connecte le signal "clicked" du bouton a la fonction qui lui correspond
            btn_save.connect('clicked', self.backup_restore_gps, 'backup')
        else:
            btn_save = gtk.Button(_('Cannot start backup (tar is missing)'))
            btn_save.set_sensitive(False)
            btn_save.props.name = 'btnSave'
            tab_box_right.pack_start(btn_save, True, False, 2)
            # On connecte le signal "clicked" du bouton a rien

        # separator
        hs = gtk.HSeparator()
        tab_box_right.pack_start(hs, True, False, 2)

        # bouton RESTAURATION
        # Si la commande tar n'existe pas, la sauvegarde ne peut etre lancee, l'affichage change et le bouton ne peut
        #     etre clique
        if self.could_backup:
            btn_restore = gtk.Button(_('Start restore...'))
            btn_restore.set_name('btnRestore')
            tab_box_right.pack_start(btn_restore, True, False, 2)
            # On connecte le signal "clicked" du bouton a la fonction qui lui correspond
            btn_restore.connect('clicked', self.backup_restore_gps, 'restore')
        else:
            btn_restore = gtk.Button(_('Cannot start restore (tar is missing)'))
            btn_restore.set_sensitive(False)
            btn_restore.set_name('btnRestore')
            tab_box_right.pack_start(btn_restore, True, False, 2)
            # On connecte le signal "clicked" du bouton a rien

        label = gtk.Label(_('Please use restore only in case of necessity !'))
        label.set_justify(gtk.JUSTIFY_CENTER)
        tab_box_right.pack_start(label, True, False, 2)

        # Creation et affichage de la frame
        event_box = self.create_custom_tab(_('Backup and Restore'), notebook,
                frame)
        notebook.append_page(frame, event_box)

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de creation de la frame POI
    def frame_poi(self, notebook):

        # --------------------------------------
        # Onglet POI
        # --------------------------------------
        frame = gtk.Frame(_('POI'))
        frame.set_border_width(10)
        frame.set_name('framePoi')
        frame.show()
        # On crée une boite verticale
        tab_box = gtk.HBox(False, 2)
        tab_box.set_name('boxPoi')
        frame.add(tab_box)
        tab_box.show()

        # On crée une boite horizontale
        tab_box_left = gtk.VBox(False, 2)
        tab_box_left.set_name('tabBoxLeftPoi')
        tab_box_left.set_size_request(120, -1)
        tab_box.add(tab_box_left)
        tab_box_left.show()
        # On crée une boite horizontale
        tab_box_right = gtk.VBox(False, 2)
        tab_box_right.set_name('tabBoxRightPoi')
        tab_box_right.set_size_request(480, -1)
        tab_box.add(tab_box_right)
        tab_box_right.show()

        # image
        image = gtk.Image()
        image.set_from_file(self.dir_pix + 'poi.png')
        tab_box_left.pack_start(image, True, False, 2)

        labelfirststep = \
            gtk.Label(_("First, you have to add POI to pyTOMTOM's database"))
        labelfirststep.set_justify(gtk.JUSTIFY_CENTER)
        tab_box_right.pack_start(labelfirststep, True, False, 2)

        # bouton
        btndb_add_poi = gtk.Button(_('Add POI (.ov2) to database...'))
        tab_box_right.pack_start(btndb_add_poi, True, False, 2)
        btndb_add_poi.connect('clicked', self.add_poi_to_database)

        # separator
        hs = gtk.HSeparator()
        tab_box_right.pack_start(hs, True, False, 2)

        labelsteptwo = \
            gtk.Label(_('Now, you can easily add or remove it from GPS...'))
        labelsteptwo.set_justify(gtk.JUSTIFY_CENTER)
        tab_box_right.pack_start(labelsteptwo, True, False, 2)

        # Liste des poi de la base
        self.poi_combo = gtk.combo_box_new_text()
        self.poi_combo.set_name('poiCombo')
        # Ajout d'une ligne vide
        self.poi_combo.append_text(_('Select POI in database'))
        self.poi_combo.append_text('----------------------')
        # selection par defaut
        self.poi_combo.set_active(0)

        # Ajout de tous les anciens poi
        if os.path.exists(self.dir_poi):
            # Ouverture du dossier des poi
            files = os.listdir(self.dir_poi)
            # print files
            # On tri par ordre alphabetique
            files.sort()
            # Pour chaque fichier
            for file in files:
                # Recuperation de l'extension du fichier pour savoir s'il s'agit d'un poi
                # f, extension = os.path.splitext( file )
                # Ajout du fichier poi, s'il s'agit d'un poi, et qu'il ne s'agit pas du fichier fourni en option
                # if( extension == ".ov2" ):
                #      self.poiCombo.append_text( f )
                self.poi_combo.append_text(file)
        tab_box_right.pack_start(self.poi_combo, True, False, 0)

        if self.current_map != False:
            labelmap = gtk.Label(_('Selected map: ') + self.current_map)
            tab_box_right.pack_start(labelmap, True, False, 2)
        btn_add_poi = gtk.Button(_('Add seleted POI on TomTom'))
        if self.current_map == False:
            btn_add_poi.set_sensitive(False)
        tab_box_right.pack_start(btn_add_poi, True, False, 2)
        btn_add_poi.connect('clicked', self.add_poi_to_tomtom)
        btn_del_poi = gtk.Button(_('Delete seleted POI from TomTom'))
        if self.current_map == False:
            btn_del_poi.set_sensitive(False)
        tab_box_right.pack_start(btn_del_poi, True, False, 2)
        btn_del_poi.connect('clicked', self.del_poi_on_tomtom)

        btndb_del_poi = gtk.Button(_('Delete POI from database...'))
        # btndbDelPoi.set_sensitive( False )
        tab_box_right.pack_start(btndb_del_poi, True, False, 2)
        btndb_del_poi.connect('clicked', self.del_poi_from_database)

        event_box = self.create_custom_tab(_('POI'), notebook, frame)
        notebook.append_page(frame, event_box)

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de creation de la frame PERSONNALISER
    def frame_personalize(self, notebook):

        # --------------------------------------
        # Onglet PERSONNALISER
        # --------------------------------------
        frame = gtk.Frame(_('Personalize'))
        frame.set_border_width(10)
        frame.set_name('Personalize')
        frame.show()
        # On crée une boite verticale
        tab_box = gtk.HBox(False, 2)
        tab_box.set_name('boxPersonalize')
        frame.add(tab_box)
        tab_box.show()

        # On crée une boite horizontale
        tab_box_left = gtk.VBox(False, 2)
        tab_box_left.set_size_request(120, -1)
        tab_box.add(tab_box_left)
        tab_box_left.show()
        # On crée une boite horizontale
        tab_box_right = gtk.VBox(False, 2)
        tab_box_right.set_size_request(480, -1)
        tab_box.add(tab_box_right)
        tab_box_right.show()

        # image
        image = gtk.Image()
        image.set_from_file(self.dir_pix + 'personalize.png')
        tab_box_left.pack_start(image, True, False, 2)

        # label
        label = \
            gtk.Label(_('Replace the startup screen of your GPS by the picture of your choice'
                      ))
        tab_box_right.pack_start(label, True, False, 2)
        # TODO verifier presence ImageMagick
        # subprocess.call( [ "convert image.jpg -resize 320x240 -background black -gravity center -extent 320x240 splash.bmp" ], shell = True )
        # bouton
        b = gtk.Button(_('Select image...'))
        tab_box_right.pack_start(b, True, False, 2)
        b.connect('clicked', self.select_img)

        event_box = self.create_custom_tab(_('Personalize'), notebook, frame)

        notebook.append_page(frame, event_box)

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de creation de la frame a propos
    def frame_about(self, notebook):

        # --------------------------------------
        # Onglet A PROPOS
        # --------------------------------------
        frame = gtk.Frame(_('About'))
        frame.set_border_width(10)
        frame.set_name('frameAbout')
        frame.show()

        # On crée une boite horizontale
        tab_box = gtk.VBox(False, 2)
        tab_box.set_name('boxAbout')
        frame.add(tab_box)
        tab_box.show()

        # image
        image = gtk.Image()
        image.set_from_file(self.dir_pix + 'pytomtom.png')
        tab_box.pack_start(image, True, False, 2)

        # On crée un label "text" (text donné en attribut)
        tab_label = gtk.Label(_('version ') + VER)
        tab_label.set_justify(gtk.JUSTIFY_CENTER)
        tab_box.pack_start(tab_label, True, False, 2)

        # self.LatestRelease()
        # bouton LatestRelease()
        btn_latest = gtk.Button(_('Need to update ?'))
        tab_box.pack_start(btn_latest, True, False, 2)
        btn_latest.connect('clicked', self.latest_release)

        # bouton acces au site web
        btn_web = gtk.Button(WEB_URL)
        tab_box.pack_start(btn_web, True, False, 2)
        btn_web.connect('clicked', self.web_connect)
        btn_web.set_tooltip_text(_('Visit homepage...'))

        event_box = self.create_custom_tab(_('About'), notebook, frame)
        notebook.append_page(frame, event_box)

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de creation de la frame quit
    def frame_quit(self, notebook):

        # --------------------------------------
        # Onglet QUITTER
        # --------------------------------------
        frame = gtk.Frame(_('Exit'))
        frame.set_border_width(10)
        frame.set_name('frameQuit')
        frame.show()

        # On crée une boite verticale
        tab_box = gtk.HBox(False, 2)
        tab_box.set_name('boxQuit')
        frame.add(tab_box)
        tab_box.show()

        # On crée une boite horizontale
        tab_box_left = gtk.VBox(False, 2)
        tab_box_left.set_size_request(120, -1)
        tab_box.add(tab_box_left)
        tab_box_left.show()
        # On crée une boite horizontale
        tab_box_right = gtk.VBox(False, 2)
        tab_box_right.set_size_request(480, -1)
        tab_box.add(tab_box_right)
        tab_box_right.show()

        # image
        image = gtk.Image()
        image.set_from_file(self.dir_pix + 'quit.png')
        tab_box_left.pack_start(image, True, False, 2)

        # label
        label = gtk.Label(_("Don't forget to cleanly unmount your TomTom!"))
        tab_box_right.pack_start(label, True, False, 2)

        # demontage propre du GPS
        btn_unmount = gtk.Button(_('Unmount'))
        # TODO: griser le btn si gps pas branche
        if self.box_init == 0:
            btn_unmount.set_sensitive(False)
        tab_box_right.pack_start(btn_unmount, True, False, 2)
        btn_unmount.connect('clicked', self.umount)

        # bouton quitter
        btn_quit = gtk.Button(stock=gtk.STOCK_QUIT)
        tab_box_right.pack_start(btn_quit, True, False, 2)
        btn_quit.connect('clicked', self.delete)
        btn_quit.set_tooltip_text(_('bye bye !'))

        event_box = self.create_custom_tab(_('Exit'), notebook, frame)
        notebook.append_page(frame, event_box)

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction parcourir pour selectionner un dossier / conservation en cas de besoin def parcourir_gps( self,entry ):
    def select_folder(self, entry):

        self.popup = gtk.FileChooserDialog(_('Open...'),
                gtk.Window(gtk.WINDOW_TOPLEVEL),
                gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, (gtk.STOCK_CANCEL,
                gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))

        if self.popup.run() == gtk.RESPONSE_OK:
            dossier = self.popup.get_filename()
            self.debug(5, dossier)
            # self.labelfolder.set_text( dossier )
            self.popup.destroy()

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction parcourir pour selectionner un fichier gtk.FILE_CHOOSER_ACTION_OPEN
    def select_img(self, entry):

        self.popup = gtk.FileChooserDialog(_('Open folder...'),
                gtk.Window(gtk.WINDOW_TOPLEVEL), gtk.FILE_CHOOSER_ACTION_OPEN,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN,
                gtk.RESPONSE_OK))
        filter = gtk.FileFilter()
        filter.set_name('images')
        filter.add_pattern('*.jpg')
        filter.add_pattern('*.png')
        self.popup.add_filter(filter)
        rep_home = os.getenv('HOME')
        self.popup.set_current_folder(rep_home)

        if self.popup.run() == gtk.RESPONSE_OK:
            img_selected = self.popup.get_filename()
            self.debug(5, img_selected)
            self.popup.destroy()
            # Verification de l'existence du fichier splash ou splashw.bmp
            if os.path.exists(self.mount + '/splashw.bmp'):
                cmd = "convert '" + img_selected \
                    + "' -resize 480x272 -background black -gravity center -extent 480x272 '" \
                    + self.mount + "/splashw.bmp'"
                p = subprocess.Popen(cmd, shell=True)
                p.wait()
                self.popup(_('OK'))
                return True
            else:
                if os.path.exists(self.mount + '/splash.bmp'):
                    cmd = "convert '" + img_selected \
                        + "' -resize 320x240 -background black -gravity center -extent 320x240 '" \
                        + self.mount + "/splash.bmp'"
                    p = subprocess.Popen(cmd, shell=True)
                    p.wait()
                    self.popup(_('OK'))
                    return True
                else:
                    self.popup(_('Error'))
                    return True

        # self.popup.destroy()
        # self.Popup( _( "OK" ) )

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction parcourir pour selectionner un fichier gtk.FILE_CHOOSER_ACTION_OPEN
    def add_poi_to_database(self, entry):

        self.popup = gtk.FileChooserDialog(_('Open folder...'),
                gtk.Window(gtk.WINDOW_TOPLEVEL),
                gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, (gtk.STOCK_CANCEL,
                gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        filter = gtk.FileFilter()
        filter.set_name('POI (*.ov2)')
        filter.add_pattern('*.ov2')
        self.popup.add_filter(filter)
        rep_home = os.getenv('HOME')
        self.popup.set_current_folder(rep_home)

        if not os.path.exists(self.dir_poi):
            # Creation du repertoire si inexistant
            os.mkdir(self.dir_poi)

        if self.popup.run() == gtk.RESPONSE_OK:
            dir_selected = self.popup.get_filename()
            self.debug(5, dir_selected)
            # on recupere juste le nom du repertoire qui servira a nommer le poi
            (filepath, filename) = os.path.split(dir_selected)
            # on cree le rep du poi dans la base
            cmd = "mkdir -p '" + self.dir_poi + filename + "'"
            p = subprocess.Popen(cmd, shell=True)
            p.wait()
            # on y copie les fichiers
            cmd = "cp '" + dir_selected + "/'* '" + self.dir_poi + filename \
                + "/'"
            p = subprocess.Popen(cmd, shell=True)
            p.wait()
            # on rajoute la nouvelle entree a la liste
            self.poi_combo.append_text(filename)

        self.popup.destroy()
        self.popup(_('POI added to database'))

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction copie du poi sur le tomtom
    def add_poi_to_tomtom(self, entry):

        selected_poi = self.poi_combo.get_active_text()
        cmd = "cp '" + self.dir_poi + selected_poi + "/'* '" + self.pt_mount \
            + "'/" + self.current_map
        p = subprocess.Popen(cmd, shell=True)
        p.wait()
        self.popup(_('POI ') + selected_poi + _(' added to TomTom'))

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction suppression du poi sur le tomtom
    def del_poi_on_tomtom(self, entry):

        selected_poi = self.poi_combo.get_active_text()
        files = os.listdir(self.dir_poi + selected_poi)
        for file in files:
            cmd = "rm -f '" + self.pt_mount + "'/" + self.current_map + "/'" \
                + file + "'"
            p = subprocess.Popen(cmd, shell=True)
            p.wait()

        self.popup(_('POI ') + selected_poi + _(' deleted from TomTom'))

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction suppression du poi sur le tomtom
    def del_poi_from_database(self, entry):
        # on supprime  les fichiers
        selected_poi = self.poi_combo.get_active_text()
        cmd = "rm -rf '" + self.dir_poi + selected_poi + "'"
        # print cmd
        p = subprocess.Popen(cmd, shell=True)
        p.wait()
        # on supprime l'entree dans le menu deroulant
        index_poi = self.poi_combo.get_active()
        self.poi_combo.remove_text(index_poi)

        self.popup(_('POI ') + selected_poi + _(' deleted from database'))

        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction test en fond de tache   NON UTILISEE
    def ma_fonction(self):
        # print "toto"
        if self.pt_mount != False:
            gps_status = 'connected'
            print gps_status
        else:
            gps_status = 'disconnected'
        # while True:
            # self.ma_fonction()
        return True

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de demarrage de la classe
    def __init__(self):

        # recuperation de pyTOMTOM en pytomtom (=<0.4.2)
        # self.Recup()
        # Recuperation de la configuration
        self.get_config()

        # Si on est pas en mode script
        if self.no_gui == False:
            # On cree la fenetre principale
            self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
            # En cas de fermeture de la fenetre, on appel la fonction Delete
            self.window.connect('delete_event', self.delete)
            self.window.set_border_width(10)
            self.window.set_title(APP)
            self.window.set_icon_from_file(self.dir_pix + 'icon.png')
            # centrage de la fenetre
            self.window.set_position(gtk.WIN_POS_CENTER)
            # timeout for tooltips
            settings = self.window.get_settings()
            settings.set_property('gtk-tooltip-timeout', 0)

            # *************************************************************************************************************
            # On cree un nouveau notebook
            notebook = gtk.Notebook()
            notebook.set_name('notebook')
            self.window.add(notebook)
            notebook.show()

            # *************************************************************************************************************
            # Construction des onglets de la fenetre principale
            self.frame_option(notebook)
            if self.box_init != 0:
                self.frame_gpsquick_fix(notebook)
                self.frame_backup_restore(notebook)
                self.frame_poi(notebook)
                self.frame_personalize(notebook)
            self.frame_about(notebook)
            self.frame_quit(notebook)

            # *************************************************************************************************************
            # Onglet que nous verrons à l'ouverture
            notebook.set_current_page(self.box_init)
            # Affichage de l'ensemble
            self.window.show_all()

        # Lancement des actions

        # Si l'option a ete fournie, lancement de la sauvegarde de la configuration
        if self.do_save:
            self.put_config()

        # Si l'option a ete fournie, lancement du GpsFix
        if self.do_gps_fix:
            self.debug(1, 'Starting GPSQuickFix')
            self.gps_quick_fix(None)

        # Si l'option a ete fournie, lancement du Backup
        if self.do_backup:
            self.debug(1, 'Starting Backup')
            self.backup_restore_gps(None, 'backup')

        # Si l'option a ete fournie, lancement de la restauration
        if self.do_restore:
            self.debug(1, 'Starting Restore')

        # Si on est en mode script, fermeture de l'application
        if self.no_gui == True:
            self.delete(None)
            return None

        if self.gps_status != 'connected':
            self.popup(_('Connect your device and reload ') + APP)
            # self.Delete( None )
            # return None

        return None


def main():
    gtk.main()
    return 0


# Entry point if not imported as module
if __name__ == '__main__':
    NotebookTomtom()
    main()
