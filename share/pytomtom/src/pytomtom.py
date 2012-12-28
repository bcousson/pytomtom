#/usr/bin/python
# -*- coding:utf-8 -*-
#----------------------------------------------- APPLICATION HEADER DEFINITION ---------------------------------------
# pyTOMTOM - Manage your TomTom !
# http://pytomtom.tuxfamily.org
# dev : Thomas LEROY
# sorry for my bad english in comments...
# python (>=2.5), python-gtk2, cabextract,  ImageMagick

#----------------------------------------------- DEVELOPPEMENT RULES DEFINITION --------------------------------------
# developpement rules
#   - Utilisation de la langue anglaise pour le nom des variables et des fonctions (pas de melange)
#   - Les noms des fonctions commencent par une majuscule, avec une majuscule a chaque nouveau mot
#   ( - les noms de fonctions commencent par une majuscule avec _ pour separer les mots )
#   - Les variables commencent par une minuscule, avec une majuscule a chaque nouveau mot
#   ( - pas de distinction entre le nom d'une variable et le nom d'une fonction )
#   - Les fonctions ont toujours une entete definissant l'utilite de la fonction, ...
#   - Le nom d'une classe s'ecrit comme le nom d'une fonction
#   - tous les textes s'utilisent avec la fonction _() afin de rendre l'application internationnale
#   - tout code ecrit deux fois est mis dans une fonction, jamais copie
#   - tous les commentaires ne sont pas ecrits avec des accents (internationalisation de l'application)
#   - pas d'espace avant (, mais un espace apres
#   - un espace avant ), mais pas d'espace apres
#   - pas d'espace avant : qui demarre un ensemble
#   - un espace avant et un apres + (concatenation de chaine)
#   - un espace apres une virgule
#   - les fonctions internes commencent par _

#---------------------------------------------------- LIBRARIES IMPORT ---------------------------------------------------------
# used to be compatible python 2.5 (with)
from __future__ import with_statement
# TODO : needed ? import pygtk
import gtk
# used to fetch cab for GPSQuickFix
import urllib2
#used to visit homepage in webbrowser
import webbrowser
# used to launch subprocess (tar, cabextract, df, ...)
import subprocess
# used to copy files and delete directory
import shutil
# used to get environment variables and operation for folder and files
import os
# used to get informations about files and directory
import os.path
# used to get date
from datetime import date
# used to get options (arg)
import getopt
# used to use systems
import sys
# used to translate text
import gettext
# used to create temp directory or file
import tempfile
# used to create timeout
import gobject
# used to create new backup file with random number
import random
# used to get terminal witdh
import termios, fcntl, struct

#----------------------------------------------- GLOBAL DEFINITION  ---------------------------------------------------------
# name,  version and homepage
App = "pyTOMTOM"
Ver = "0.6 alpha 1"
WebUrl = "http://pytomtom.tuxfamily.org"

# i18n (internationalisation) /usr/share/locale
gettext.bindtextdomain('pytomtom', '../share/locale')
gettext.textdomain('pytomtom')
_ = gettext.gettext

# TODO : en mode texte non lance par un terminal, un message d'erreur arrive, il n'empeche pas le lancement
#        du logiciel ni ses actions, mais il serait plus propre de ne pas l'avoir

#----------------------------------------------- VERIFICATIONS DES PRE-REQUIS ------------------------------------------------
# Verify to running Linux - posix system
if( os.name != "posix" ):
    print "You are not runnig Linux operating system"
    sys.exit( 2 )
# TODO : needed ? Verify python  >=2.0
#pygtk.require('2.0')

#----------------------------------------------- DEFINITION DE LA CLASSE PRINCIPALE ------------------------------------------
class NotebookTomtom:

    #------------------------------------------ DEFINITION DES VARIABLES GLOBALES -------------------------------------------
    # config directory
    dir = os.getenv( "HOME" ) + "/." + App
    # config file
    configFile = App + ".cfg"
    # ephem directory on tomtom
    dest = "/ephem"
    # poi database directory
    dirPoi = dir + "/poi/"
    # backup directory
    dirBackup = dir + "/backup"
    # file needed for recognize a tomtom
    ttgo = "/tomtom.ico"
    # pix directory (for pytomtom)
    dirPix = "../share/pytomtom/pix/"
    # mount point, false = unknow
    ptMount = False
    # mount point size (octet)
    ptMountSize = -1
    # all mount points, by default empty
    ptMounts = []
    # tomtom model, false = unknow
    model = False
    # current map in use, false = unknow
    CurrentMap = False
    # tab at pytomtom start, by default "About"
    # 0=options, 1=GPSQuickFix, 2=Save&Restore, 3=poi, 4=personalize, 5=about, 6=quit
    boxInit = 5
    # chipset siRFStarIII models
    siRFStarIII = [
        "Carminat",
        "GO 300",
        "GO 500",
        "GO 510",
        "GO 520",
        "GO 530",
        "GO 540 LIVE",
        "GO 630",
        "GO 700",
        "GO 710",
        "GO 720",
        "GO 730",
        "GO 910",
        "GO 920",
        "GO 930",
        "ONE 1st Edition",
        "ONE 2nd Edition (S)",
        "RIDER",
        "RIDER 2nd Edition"]
    # chipset globalLocate models
    globalLocate = [
        "GO 740 LIVE",
        "GO 750 LIVE",
        "GO 940 LIVE",
        "GO 950 LIVE",
        "GO LIVE 820",
        "GO LIVE 825",
        "GO Live 1000",
        "GO Live 1005",
        "ONE 2nd Edition (G)",
        "ONE 3rd Edition",
        "ONE 30 Series",
        "ONE 130",
        "ONE IQ Routes",
        "ONE White Pearl",
        "ONE XL",
        "Start",
        "Start 2",
        "Via 110",
        "Via 120",
        "Via 125",
        "XL 30 Series",
        "XL IQ Routes",
        "XL LIVE IQ Routes"]
    # all models
    # TODO : not use append, extend instead ?
    models = []
    for model in siRFStarIII:
        models.append( model )
    for model in globalLocate:
        models.append( model )
    # alphabetic sort
    models.sort()

    # debug level, =< 1 by default
    debug = 1

    # log, sys.stdout (= print)
    logFileName = dir + "/" + os.path.basename( sys.argv[ 0 ] ) + ".log"
    # ie : logFile = open( logFileName, "w" ) # erase an write new
    # ie : logFile = open( logFileName, "a" ) # add and write
    # = print
    logFile = sys.stdout

    # by default log isn't overwrited, this option to overwrite log
    overwriteLog = False
    # launching without gui (script mode), false by default
    noGui = False
    # launching witout do external action (to debug, ie gpsquickfix, backup, restore)
    noExec = False
    # launch GPSQuickFix
    doGpsFix = False
    # launch backup
    doBackup = False
    # launch save
    doSave = False
    # launch restore
    doRestore = False
    # backup or restore launched process
    procBackup = None
    # filename for restore or backup
    fileName = False
    # progression bar for restore or backup
    progressionBar = None
    # progression bar size for gui (in text mode, size is calculated /terminal)
    progressionBarSize = 120
    # estimated time remind
    configTimeRemind = True
    # time passed
    configTimePassed = False
    # estimated total time
    configTimeTot = True
    # tempo for progress bar
    tempo = None
    # tempo delay for progress bar
    tempoDelay = 3000
    # timestamp at start, to calculate estimated time remind and estimated total time
    tempoStartTime = None
    # minuteur pour le refraichissement du combo contenant la liste des points de montages
    tempoCombo = None
    # Verification de la possibilite d'effectuer le GPSFix (presence de cabextract)
    couldGpsFix = True
    # Verification de la possibilite d'effectuer le backup (presence de tar)
    couldBackup = True
    # Si l'utilisateur veut quitter avant la fin d'un sous-processus, la sauvegarde ou la restauration finissent puis l'application quitte
    quit = False
    # gps status at start
    gpsStatus = "disconnected"

    # objet graphique window
    window = None
    # objet graphique de la liste des points de montage
    ptCombo = None

    #------------------------------------------ DEFINITION DES FONCTIONS DE LA CLASSE ---------------------------------------
    #

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction d'affichage des informations
    def Debug( self, niveau, text ):

        # Affichage uniquement si le niveau general de debug est superieur au niveau du debug fourni
        if( niveau <= self.debug ):
            # Ecriture dans le fichier de log
            self.logFile.write( str( date.today() ) + " " + text + "\n" )
            # flush pour un affichage immediat
            self.logFile.flush()
        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction d'affichage du nom et de la version de l'application
    def PrintVersion( self ):

        print( "" )
        print( App )
        print( Ver )

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # conversion pyTOMTOM to pytomtom (=< 0.4.2 to 0.5)
    # later, we'll suppress this... (or not)
    def Recup( self ):

        # old config directory
        old_dir = os.getenv( "HOME" ) + "/.pyTOMTOM"
        if not( os.path.exists( self.dir ) ):
            # new config directory if not exist
            os.mkdir( self.dir )
        if ( os.path.exists( old_dir ) ):
            oldfiles = os.listdir( old_dir )
            for file in oldfiles:
                # move to new config directory
                shutil.move( old_dir + "/" + file, self.dir + "/" + file )

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # what's the latest pytomtom release ?
    def LatestRelease( self, widget ):

        try:
            url = "http://tomonweb.2kool4u.net/pytomtom/LATEST"
            request = urllib2.Request( url, None )
            urlFile = urllib2.urlopen( request )
            tempFile = tempfile.NamedTemporaryFile()
            tempFile.write( urlFile.read() )
            tempFile.flush()
            urlFile.close()
            with open( tempFile.name, "rb" ) as latest:
                line = latest.readline()
                line = line[:-1]
                latest.close()
            if( Ver == line ):
                msg = ( _( "No need to update. You use the latest stable release." ) )
                self.Popup( msg )
            else:
                msg = ( _( "You can update. The latest stable release is " ) + line )
                self.Popup( msg )

        except:
            msg = ( _( "Impossible to fetch data" ) )
            self.Popup( msg)


    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # open pytomtom homepage in browser
    def WebConnect( self, widget ):

        webbrowser.open( WebUrl )
        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction d'affichage de l'utilisation des options
    def Usage( self ):

        # Utilisation de sysr.argv[ 0 ] afin d'avoir toujours le bon nom de l'executable
        print( "" )
        print( "usage: " + "python " + os.path.basename( sys.argv[ 0 ] ) + " [option]" )
        print( "" )
        print( "    -h, --help                                 " + "This online help" )
        print( "    -V, --version                              " + "Print the name and version of this software" )
        print( "    -d, --debug         niv                    " + "Debugging level, from 0 to 9" )
        print( "    -l, --log-file      file-to-log            " + "Name of traces log file" )
        print( "    -x, --overwrite-log                        " + "Overwrite log file (default is append)" )
        print( "        --no-exec                              " + "Show commands to be executed but do not execute them" )
        print( "        --print-time-passed                    " + "Show elapsed time in progress bar" )
        print( "        --print-time-remind                    " + "Show remaining time in progress bar" )
        print( "        --print-time-tot                       " + "Show total estimated time in progress bar" )
        print( "    -n, --no-gui                               " + "Usage in text mode" )
        print( "    -s, --save-config                          " + "Save configuration file" )
        print( "    -g, --do-gpsfix                            " + "Start update of GPSQuickFix" )
        print( "    -b, --do-backup                            " + "Start backup operation in file "
                + self.dir + "/sv-[date-du-jour]-[model].tar[.gz|.bz] "
                + "\n                                               or provided with -f" )
        print( "    -r, --do-restore                           " + "Start restore operation from file "
                + self.dir + "/sv-[date-du-jour]-[model].tar[.gz|.bz]"
                + "\n                                               or provided with -f" )
        print( "    -f, --file          file-to-save           " + "Path of backup/restore file" )
        print( "    -p, --ptmount       dir                    " + "Mounting point of the TomTom" )
        print( "    -m, --model         model                  " + "TomTom model, in the list:" )
        # Liste des modeles
        for model in self.models:
            print( "                                                     '" + model + "'" )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de recuperation des options
    def GetOpts( self ):

        # initialisation des variables
        ptMount = False
        model = False
        debug = False
        err = False
        logFile = None

        # On teste la recuperation des arguments
        try:
            # getopt.getopt decoupe la ligne (l'ensemble des arguments : sys.argv[1:]) en deux variables, les options et les arguments de la commande
            #        l'ordre des options importe peu pour la technique, cependant, afin de ne pas mettre deux fois la meme lettre, il est plus
            #        simple de respecter l'ordre alphabetique
            opts, args = getopt.getopt( sys.argv[1:], "bd:f:ghl:m:np:rsxV",
                    [ "do-backup", "debug=", "file=", "do-gpsfix", "help", "log-file=", "model=", "no-gui", "ptmount=", "do-restore",
                            "save-config", "overwrite-log", "version",
                            "no-exec", "print-time-passed", "print-time-remind", "print-time-tot" ] )
        # Si le test ne fonctionne pas
        except getopt.GetoptError, err:
            # affichage de l'erreure
            self.Debug( 0, str( err ) ) # Affichera quelque chose comme "option -a not recognized"
            # Affichage de l'utilisation des options
            self.Usage()
            sys.exit( 2 )

        # Pour chaque option et ses arguments de la liste des options
        for opt, argument in opts:
            if opt in ( "-b", "--do-backup" ):
                self.doBackup = True
                self.Debug( 5, "Option Backup" )
            elif opt in ( "-d", "--debug" ):
                # Verification de l'option fournie faite a la fin
                debug = argument
            elif opt in ( "-f", "--file" ):
                self.fileName = os.path.realpath( argument )
                self.Debug( 5, "Option File name: " + self.fileName )
            elif opt in ( "-g", "--do-gpsfix" ):
                self.doGpsFix = True
                self.Debug( 5, "Option GPSQuickFix" )
            elif opt in ( "-h", "--help" ):
                self.Usage()
                sys.exit()
            elif opt in ( "-l", "--log-file" ):
                logFile = argument
            elif opt in ( "-m", "--model" ):
                # Verification du bon choix du modele faite a la fin
                model = argument
            elif opt in ( "-n", "--no-gui" ):
                self.noGui = True
                self.Debug( 5, "Option Script mode" )
            elif opt in ( "-p", "--ptmount" ):
                # Verification du bon choix du point de montage faite a la fin
                ptMount = argument
            elif opt in ( "-r", "--do-restore" ):
                self.doRestore = True
                self.Debug( 5, "Option Restore" )
            elif opt in ( "-s", "--save-config" ):
                self.doSave = True
                self.Debug( 5, "Option Save configuration" )
            elif opt in ( "-x", "--overwrite-log" ):
                self.overwriteLog = True
                self.Debug( 5, "Option Overwrite configuration" )
            elif opt in ( "-V", "--version" ):
                self.PrintVersion()
                sys.exit()
            elif opt in ( "--no-exec" ):
                self.noExec = True
                self.Debug( 5, "Option Without execution" )
            elif opt in ( "--print-time-passed" ):
                self.configTimePassed = True
                self.Debug( 5, "Option Print elapsed time in progress bar" )
            elif opt in ( "--print-time-remind" ):
                self.configTimeRemind = True
                self.Debug( 5, "Option Print remaining time in progress bar" )
            elif opt in ( "--print-time-tot" ):
                self.configTimeTot = True
                self.Debug( 5, "Option Print total time in progress bar" )
            else:
                # Si l'option est mise dans getopt mais n'est pas traite ici
                self.Debug( 0, "Option No action" )

        # Verifications diverses

        # Changement de fichier de log
        if( logFile != None ):
            # Choix du mode d'ecriture du fichier de log, par defaut en ajout, si l'option est fournie, on passe en ecrasement
            if( self.overwriteLog == True ):
                option = "a"
            else:
                option = "w"

            # On test l'ecriture dans le nouveau fichier de log
            try:
                # Pour ne pas perdre l'ancien fichier, on ouvre le nouveau dans une nouvelle variable
                logFile = open( logFile, option )
                # Si tout s'est bien passe, on ferme l'ancien fichier (sauf s'il s'agit de stdout)
                if( self.logFile != sys.stdout ):
                    self.logFile.close()
                # Puis on rattache le nouveau fichier a la variable globale
                self.logFile = logFile
            except:
                # S'il y a une erreur, on affiche un message d'erreur (dans l'ancien fichier de log)
                self.Debug( 1, "Impossible to change log file" )
        else:
            # S'il n'y a pas de demande de nouveau fichier mais simplement d'excrasement du fichier de log (et qu'il ne s'agit pas
            # de stdout, et re-ouvre (fermeture puis re-ouverture) le fichier de log en ecrasement
            if( self.logFile != sys.stdout and self.overwriteLog == True ):
                self.logFile.close()
                self.logFile = open( self.logFileName, "w" )

        # Si les options de sauvegarde et de restauration sont founies en meme temps, il y a erreur
        if( self.doBackup and self.doRestore ):
            self.Debug( 0, "Incompatible options -b and -r" )
            # Afin que toutes les options soient testees plutot que de stopper sur la premiere puis la seconde...
            err = True

        # Verification que le modele donne fait partie de la liste des modeles existants
        if not( model == False ):
            if( model in self.models ):
                self.model = model
                self.Debug( 5, "Selected model: " + self.model )
            else:
                self.Debug( 0, "Invalid model " + str( model ) )
                # Afin que toutes les options soient testees plutot que de stopper sur la premiere puis la seconde...
                err = True

        # Verification du point de sauvegarde
        if not( ptMount == False ):
            if( self.IsPtMount( ptMount ) ):
                self.ptMount = ptMount
                self.Debug( 5, "Selected mounting point: " + self.ptMount )
            else:
                self.Debug( 0, "Invalid mounting point argument: " + ptMount )
                # Afin que toutes les options soient testees plutot que de stopper sur la premiere puis la seconde...
                err = True

        # Verification que le niveau de debug est compris entre 0 et 9
        if not( debug == False ):
            try:
                if( int( debug ) >= 0 and int( debug ) <= 9 ):
                    self.debug = int( debug )
                    self.Debug( 5, "Debugging level argument " + str( int( debug ) ) )
                else:
                    self.Debug( 1, "Mauvais argument pour l'option de deboggage " + str( int( debug ) ) )
            except:
                self.Debug( 1, "Debugging level argument is not an int " + debug )

        # Si on a une erreur, on arrete le programme
        if( err ):
            self.Usage()
            sys.exit( 2 )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de lecture des variables d'environnement
    def GetVariables( self ):

        # Lecture du point de montage (variable PYTOMTOM_PTMOUNT)
        env = os.getenv( "PYTOMTOM_PTMOUNT", False )
        if not( env == False ):
            self.ptMount = str( env )
            self.Debug( 5, "Selected mounting point: " + str( env ) )

        # Lecture du modele PYTOMTOM_MODELE
        env = os.getenv( "PYTOMTOM_MODELE", False )
        if not( env == False ):
            self.model = str( env )
            self.Debug( 5, "Selected model: " + str( env ) )

        # Lecture de l'affichage de la barre de progression
        env = os.getenv( "PYTOMTOM_CONFIG_TIME_PASSED", False )
        if not( env == False ):
            if( env == "False" ):
                self.configTimePassed = False
            elif( env == "True" ):
                self.configTimePassed = True
            self.Debug( 5, "Elapsed time: " + str( env ) )

        # Lecture de l'affichage de la barre de progression
        env = os.getenv( "PYTOMTOM_CONFIG_TIME_REMIND", False )
        if not( env == False ):
            if( env == "False" ):
                self.configTimeRemind = False
            elif( env == "True" ):
                self.configTimeRemind = True
            self.Debug( 5, "Remaining time: " + str( env ) )

        # Lecture de l'affichage de la barre de progression
        env = os.getenv( "PYTOMTOM_CONFIG_TIME_TOT", False )
        if not( env == False ):
            if( env == "False" ):
                self.configTimeTot = False
            elif( env == "True" ):
                self.configTimeTot = True
            self.Debug( 5, "Total time: " + str( env ) )

        # Afin de valider le mode graphique, on verifie la variable d'environnement DISPLAY
        env = os.getenv( "DISPLAY", False )
        if( env == False or env == "" ):
            self.noGui = True
            self.Debug( 5, "Option Script mode" )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de lecture des donnees de configuration
    def GetConfig( self ):

        # La lecture du fichier de configuration, puis des options et enfin des variables d'environnement
        # permet de definir l'ordre de preference des donnees si les donnees sont fournies sous differentes formes

        # Verification de l'existence du repertoire de configuration
        if not( os.path.exists( self.dir ) ):
            # Creation du repertoire si inexistant
            os.mkdir( self.dir )
            # Verification apres creation afin de valider le systeme
            if not( os.path.exists( self.dir ) ):
                self.Debug( 0, "Impossible to create configuration file " + self.dir )
                sys.exit( 2 )
        else:
            # Verification que le dossier de configuration en est bien un
            # TODO : verification en cas de lien vers un dossier plutot qu'un dossier
            if( os.path.isdir( self.dir ) ):
                # Verification de l'existence du fichier de configuration
                if( os.path.exists( self.dir + "/" + self.configFile ) ):
                    # Ouverture du fichier de configuration en lecture
                    with open( self.dir + "/" + self.configFile, "rb" ) as config:
                        # Lecture des lignes
                        line = config.readline()
                        while( line ):
                            # suppression des \n de fin de ligne
                            line = line[:-1]
                            # Le fichier se presente sous la forme nom=valeur, on decoupe selon le =
                            line = line.split( '=' )
                            # Suppression des espaces inutiles en debut et fin de mot
                            name = line[ 0 ].strip()
                            # On traite en deux cas, soit le parametre est un string, soit un bouleen
                            if( name in ( "ptMount", "model" ) ):
                                # setattr permet d'associer la valeur a l'attribut fourni par son nom au format str
                                # On supprime naturellement les espaces inutiles en debut et fin de mot
                                setattr( self, name, line[ 1 ].strip() )
                            #      deuxieme cas, s'il s'agit d'un bouleen
                            elif( name in ( "configTimePassed", "configTimeRemind", "configTimeTot" ) ):
                                if( line[ 1 ].strip() == "True" ):
                                    setattr( self, name, True )
                                else:
                                    setattr( self, name, False )

                            # lecture de la prochaine ligne
                            line = config.readline()
                    # Fermeture du fichier de configuration
                    config.close()
            else:
                self.Debug( 0, "Configuration path is not a directory " + self.dir )
                sys.exit( 2 )

        # Lecture de la carte utilisee

        # si carminat TODO mount loopdir
        if( self.model == "Carminat" ):
            if not( self.ptMount == False ):
                desktop_environment = 'generic'
                superman = ''
                if os.environ.get('KDE_FULL_SESSION') == 'true':
                    desktop_environment = 'kde'
                    superman = 'kdesu'
                elif os.environ.get('GNOME_DESKTOP_SESSION_ID'):
                    desktop_environment = 'gnome'
                    superman = 'gksudo'

                #cmd = ( "cp '" + self.ptMount + "/loopdir/ext3_loopback' /tmp && mkdir /tmp/vfs && gksudo 'mount -w /tmp/ext3_loopback /tmp/vfs -t ext3 -o loop'" )
                cmd = ( "cp '" + self.ptMount + "/loopdir/ext3_loopback' /tmp && mkdir /tmp/vfs && " + superman + " 'mount -w /tmp/ext3_loopback /tmp/vfs -t ext3 -o loop'" )
                print desktop_environment
                print cmd
                p = subprocess.Popen( cmd, shell=True )
                p.wait()
                # TODO methode universelle ou monter un systeme sans etre root, mais la je reve...

                fileTTGObif = os.path.join( "/tmp/vfs", "CurrentMap.dat" )

        #sinon
        else:
            self.ptMount = str( self.ptMount )
            fileTTGObif = os.path.join( self.ptMount, "CurrentMap.dat" ) # -->  /media/cle usb 4g/ttgo.bif [OK]
            #fileTTGObif = str( self.ptMount ) + "/CurrentMap.dat" # --> /media/cle usb 4g/ttgo.bif [OK]

        print str( fileTTGObif )

        if( os.path.exists( str( fileTTGObif ) ) ):
            with open( fileTTGObif, "rb" ) as ttgobif:
                line = ttgobif.readline()
                line = line[:-2]
                line = line.split( "/" )
                self.CurrentMap = str( line[-1] )
                #print self.CurrentMap
            ttgobif.close()

        # Lecture des options
        self.GetOpts()
        # Lecture des variables d'environnement
        self.GetVariables()

        # Si le point de montage ou le modele n'est pas defini, il faut le definir -> passage sur la fenetre de gestion des options
        #       de meme si le point de montage n'est pas valide
        if( self.ptMount == False or self.IsPtMount( self.ptMount ) == False or self.model == False ):
            self.boxInit = 0
            #self.Popup( _( "Connect your device and restart " ) + App )

        # Validation des possibilites de l'application (verification des dependances externes)
        # Lancement de la commande which cabextract qui precise l'emplacement de cabextract, renvoi 0 si trouve, 1 sinon
        p = subprocess.Popen( "which cabextract > /dev/null", shell=True )
        if( p.wait() != 0 ):
            self.Debug( 1, "cabextract is not installed" )
            self.couldGpsFix = False

        # Lancement de la commande which tar qui precise l'emplacement de cabextract, renvoi 0 si trouve, 1 sinon
        p = subprocess.Popen( "which tar > /dev/null", shell=True )
        if( p.wait() != 0 ):
            self.Debug( 1, "tar is not installed"  )
            self.couldBackup = False

        # Affichage des informations de deboggage
        self.Debug( 1, "Application: " + App + " - Version: " + Ver )
        self.Debug( 1, "Mounting point used: " + str( self.ptMount ) )
        self.Debug( 1, "Model used: " + str( self.model ) )
        self.Debug( 1, "Curent map: " + str( self.CurrentMap ) )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de mise a jour et d'enregistrement des options par le formulaire
    def OnUpdate( self, entry ):

        # Recuperation des differents parametres du formulaire
        model = self.modeleCombo.get_model()
        index = self.modeleCombo.get_active()
        self.model = str( model[ index ][ 0 ] )
        # Pas de verification du modele puisque le choix s'effectue a partir d'une liste fournie par l'application, aucun risque d'erreur

        ptMount = self.ptCombo.get_model()
        index = self.ptCombo.get_active()
        if( self.IsPtMount( str( ptMount[ index ][ 0 ] ) ) ):
            self.ptMount = str( ptMount[ index ][ 0 ] )

        # Enregistrment des options
        self.PutConfig()
        self.Popup( _( "Reload " ) + App + _( " to use this settings." ) )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de sauvegarde de la configuration
    def PutConfig( self ):

        # Verification des donnees a sauvegarder
        if not( self.ptMount and self.model ):
            self.Debug( 0, "Cannot write data: " + "mounting point = '" + str( self.ptMount )
                    + "' - model = '" + str( self.model ) + "'" )
            sys.exit(2)

        # Sauvegarde des donnees dans le fichier de configuration
        try:
            configFile = open( self.dir + "/" + self.configFile, "wb" )
            # L'enregistrement des options s'effectue sous le forme nom=valeur
            # getattr permet de recuperr la valeur de l'attribut fourni par son nom au format str
            for option in ( "ptMount", "model", "configTimePassed", "configTimeRemind", "configTimeTot" ):
                configFile.write( option + "=" + str( getattr( self, option ) ) + "\n" )
        finally:
            # Fermeture du fichier, qu'il y ait une erreur ou non
            configFile.close()

        # Affichage des informations de deboggage
        self.Debug( 1, "TomTom: " + str( self.model ) + " ::saved::" )
        self.Debug( 1, "Mounting point: " + str( self.ptMount ) + " ::saved::" )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de recherche des points de montage disponibles
    def GetPtMounts(self):

        # Mise a zero de la liste
        self.ptMounts = []
        # Recuperation de la liste des points de montage de type vfat, avec leur taille
        ptMounts = self.GetPtWithSize( "vfat" )
        # Pour chaque point de montage
        for ptMountSize, ptMount in ptMounts:
            if( ptMountSize == -1 ):
                self.Debug( 5, "No mounting point" ) #5
                return True

            # Validation du point de montage
            if( self.IsPtMount( ptMount ) ):
                self.ptMounts.append( [ ptMountSize, ptMount ] )

        # Affichage des informations de deboggage
        self.Debug( 5, "List of mounting points " + str( self.ptMounts ) ) #5

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de validation du point de montage
    def IsPtMount(self, mountPoint):

        # Si le point de montage n'est pas fourni ou est faux
        if( mountPoint == False ):
            return False

        # Verification de l'existence du fichier tomtom.ico pour valider qu'il s'agit bien d'un point de montage d'un tomtom
        self.Debug( 6, "Testing mounting point " + mountPoint )
        if( os.path.exists( mountPoint + self.ttgo ) ):
            self.Debug( 5, "Valid mounting point: " + mountPoint )
            self.gpsStatus = "connected"
            #print "test : ok : tomtom"
            return True

        # Dans tous les autres cas, le point de montage n'est pas valide
        #print "test : ERROR : not a tomtom"
        return False

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction demontage
    def UMount(self, mountPoint):
        cmd = ( "umount '" + self.ptMount +"'" )
        p = subprocess.Popen( cmd, shell=True )
        p.wait()
        #self.btnUnmount.set_sensitive( False )
        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction GPSQUICKFIX, mise a jour des donnees de l'emplacement des satellites (a effectuer une fois par semaine)
    def GpsQuickFix(self, widget):
        print "starting GpsQuickFix..."

        # Si cabextract n'existe pas, on ne fait rien
        if( self.couldGpsFix == False ):
            return False

        # Verification du point de montage
        if not( self.IsPtMount( self.ptMount ) ):
            self.Debug( 1, "Invalid mounting point: " + self.ptMount )
            return False

        # Aucune verification du modele car il provient d'une liste pre-definie

        # Definition du dossier de destination
        dir = str( self.ptMount + self.dest )

        # Verification de l'existence du du dossier ephem
        self.Debug( 6, "Testing ephem directory " + dir )
        if( os.path.exists( dir ) ):
            self.Debug( 5, "Valid directory: " + dir )
        else:
            self.Debug( 5, "Creating ephem directory" )
            # on cree le repertoire ephem si il n'existe pas
            cmd = ( "mkdir " + dir )
            p = subprocess.Popen( cmd, shell=True )
            p.wait()

        if self.model in self.siRFStarIII: # si le tomtom possede un chipset SiRFStarIII
            url = "http://home.tomtom.com/download/Ephemeris.cab?type=ephemeris&amp;eeProvider=SiRFStarIII&amp;devicecode=2"
            self.Debug( 6, "chipset SiRFStarIII : " + url )
        else: # sinon (si le tomtom possede un chipset globalLocate)
            url = "http://home.tomtom.com/download/Ephemeris.cab?type=ephemeris&amp;eeProvider=globalLocate&amp;devicecode=1"
            self.Debug( 6, "chipset globalLocate : " + url )

        # Definition d'une requete
        request = urllib2.Request( url, None )
        # Ouverture de la requete
        try:
            # Si l'on veut l'execution, on lance la recuperation de l'url
            if( self.noExec == False ):
                urlFile = urllib2.urlopen( request )
        except:
            self.Debug( 1, "Impossible to fetch URL: " + url )
            return False

        # Autant de try imbrique afin de fournir des messages justes, et de supprimer correctement les fichiers et dossiers temporaires
        # Le cab est recupere dans un fichier temporaire, puis extrait dans un dossier temporaire
        try:
            # Creation d'un repertoire temporaire pour extraire le cab telecharge
            tempDirName = tempfile.mkdtemp()
            self.Debug( 5, "Creating temporary directory: " + tempDirName )
            try:
                # Creation d'un fichier temporaire pour le telechargement du cab
                tempFile = tempfile.NamedTemporaryFile()
                self.Debug( 5, "Creating temporary file: " + tempFile.name )
                try:
                    self.Debug( 5, "Fetching data: " + url )
                    # Si l'on veut une execution, on telecharge le cab
                    if( self.noExec == False ):
                        tempFile.write( urlFile.read() )
                        tempFile.flush()
                        urlFile.close()
                    try:
                        # Extraction du cab seulement si l'on veut l'execution, sinon un simple affichage de ce que l'on aurait fait
                        if( self.noExec == False ):
                            cmd = ( "cabextract -d " + tempDirName
                                    + " " + tempFile.name + "; touch " + tempDirName + "/*" )
                        else:
                            cmd = ( "echo cabextract -d " + tempDirName
                                    + " " + tempFile.name + "; echo touch " + tempDirName + "/*" )
                        self.Debug( 5, "Launching command " + cmd )
                        # Lancement du processus
                        p = subprocess.Popen( cmd, shell=True )
                        p.wait()
                        try:
                            # Deplacement de tous les fichiers du cab vers la destination
                            #     Ceci evite de faire une difference entre les deux modeles de chipset
                            files = os.listdir( tempDirName )
                            for file in files:
                                self.Debug( 5, "Moving file to final destination: "
                                        + tempDirName + "/" + file + " -> " + self.ptMount + self.dest + "/" + file )
                                # ATTENTION : si le fichier destination est un repertoire, et que le fichier existe
                                #             shutil.move fait une erreur, il faut donc preciser le fichier de destination
                                #             pour l'ecraser, et non simplement le repertoire de destination
                                shutil.move( tempDirName + "/" + file, self.ptMount + self.dest + "/" + file )
                        except:
                            self.Debug( 0, "Impossible to move data" )
                    except:
                        self.Debug( 0, "Impossible to extract data" )
                except:
                    self.Debug( 0, "Impossible to fetch data" )
            except:
                self.Debug( 0, "Impossible to create temporary file" )
            finally:
                # Fermeture propre du fichier temporaire (avec sa suppression) dans tous les cas (meme si un probleme survient)
                tempFile.close()
        except:
            self.Debug( 0, "Impossible to create temporary directory" )
        finally:
            # Suppression du dossier temporaire dans toça c'est la dernière, supprime tout le reste...us les cas (meme si un probleme survient)
            shutil.rmtree( tempDirName )

        # Affichage de la fin de l'execution, en popup si l'on est pas en mode script
        if( self.noGui == False ):
            self.Popup( _( "GPSQuickFix completed" ) )
        self.Debug( 1, "GPSQuickFix completed" )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de recuperation du nom et de la taille des partitions locales montees, limite par un type de systeme, ou/et un point de montage
    def GetPtWithSize( self, type = None, ptMount = None ):

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
        cmd = "df -B 1 -TlP"
        if not( type == None ):
            cmd += "t " + type + " "
        if not( ptMount == None ):
            cmd += " \"" + ptMount + "\""
        #cmd += " 2> /dev/null | tail -n +2 | tr -s ' ' | cut -d ' ' -f 4,7 --output-delimiter=,"
        cmd += " 2> /dev/null | tail -n +2 | tr -s ' ' | cut -d ' ' -f 4,7-"

        # Lancement de la commande, avec recuperation du stdout dans le processus actuel
        self.Debug( 5, "launching command: " + cmd ) #5
        p = subprocess.Popen( cmd, stdout = subprocess.PIPE, shell=True )
        res = []
        # Lecture du resultat
        for line in p.stdout:
            # Suppression du \n de la ligne
            line = line[ : -1 ]
            line = line.split( ' ', 1 )
            self.Debug( 5, "Command result: " + str( int( line[ 0 ] ) ) + " -> " + line[ -1 ] ) #5
            #res.append( [ int( line[ 0 ] ), line[ 1 ] ] )
            res.append( [ int( line[ 0 ] ), line[ -1 ] ] )
        p.wait()

        if( res == [] ):
            # le resultat de la fonction est une liste de liste contenant la taille et le nom du point de montage
            return( [ [ -1, None ] ] )

        # Renvoi des donnees collectees
        return res

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de recherche d'un enfant de self.window, le nom fourni sous la forme nom_frame.nom_box.... 7
    def SearchObj( self, name ):

        # TODO : existe-t-il deja une fonction plus rapide ?
        # Decoupage du nom par le separateur "."
        name = name.split( '.' )

        # On commence au niveau self.window
        objParent = self.window
        self.Debug( 7, "Searched object: " + str( name ) )

        # Pour tous les niveaux du nom fourni
        for i in range( 0, len( name ) - 1, 1 ):
            self.Debug( 7, "Scanning level: " + str( i ) )

            # Enfant non trouve
            find = False

            # Pour chaque enfant
            for objChild in objParent:
                self.Debug( 7, "     Object scanned: " + objChild.get_name() )
                # Si le nom correspond
                if( objChild.get_name() == name[ i ] ):
                    self.Debug( 7, "Object found" )
                    # Le parent devient l'enfant pour continuer la recherche au niveau suivant
                    objParent = objChild
                    # On a bien trouve l'enfant
                    find = True
                    break

            # Si l'enfant n'est pas trouve a ce niveau, on arrete tout
            if( find == False ):
                return None

        # retour de l'enfant, comme le parent est devenu l'enfant, il suffit de retourner le parent (on est sur qu'il est defini)
        return objParent

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction de remplacement image de demarrage avec toutes les verifications utiles
    def ChangeStartImg( self, widget ):

        # TODO : mettre en place la reconnaissance des noms des images a remplacer
        if ( os.path.exists( self.ptMount +"/splash.bmp" ) ):
            return True #ecran normal n
            # subprocess.call( [ "convert image.jpg -resize 320x240 -background black -gravity center -extent 320x240 splash.bmp" ], shell = True )
        else:
            if ( os.path.exists( self.ptMount +"/splashw.bmp" ) ): #elif ?? non
                return True #ecran widescreen w
                # subprocess.call( [ "convert image.jpg -resize 480x272 -background black -gravity center -extent 480x272 splash.bmp" ], shell = True )

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de creation d'un nom de fichier de sauvegarde
    def GetNewFileName( self, uniq = False ):

        # si l'option uniq est fournie, on ajoute un nombre aleatoire
        if( uniq == False ):
            return( self.dirBackup + "/sv-" + str( date.today() ) + "-" + self.model + ".tar" )
        else:
            return( self.dirBackup + "/sv" + str( random.randint( 1, 50 ) ) + "-" + str( date.today() ) + "-" + self.model + ".tar" )

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction de lancement du Backup et de la restauration avec toutes les verifications utiles
    def BackupRestoreGPS( self, widget, type ):

        # Verification du point de montage
        if not( self.IsPtMount( self.ptMount ) ):
            self.Debug( 1, "Invalid mounting point: " + self.ptMount )
            return False

        # Recuperation du nom du fichier de sauvegarde
        files = self.saveFileCombo.get_model()
        index = self.saveFileCombo.get_active()
        if( files[ index ][ 0 ] == "" ):
            self.Debug( 2, "Invalid file selected for " + _( type ) )
            return False
        self.fileName = files[ index ][ 0 ]
        self.Debug( 1, "File for " + _( type ) + ": " + self.fileName )

        if( type == "restore" ):
            if not( os.path.exists( self.fileName ) ):
                self.Debug( 1, "Backup file not found" )
                return False

        if( self.noGui == False ):
            obj = self.SearchObj( "notebook.frameSaveRestore.boxSaveRestore.btnSave" )
            if( obj != None ):
                obj.set_sensitive( False )
            obj = self.SearchObj( "notebook.frameSaveRestore.boxSaveRestore.btnRestore" )
            if( obj != None ):
                obj.set_sensitive( False )

        # Verification de l'espace disponible par rapport a l'espace initial,

        # Recuperation d'un tableau de toutes les partitions de type
        #     les donnees sont sur la ligne 0 puisque nous n'avons qu'une seule ligne
        self.ptMountSize = self.GetPtWithSize( "vfat", self.ptMount )
        # Recuperation du nom de la partition impactee,
        #     en effet, si l'on fournit /boot, on retrouve / car /boot n'est pas monte et fait partie du systeme /
        self.ptMount = self.ptMountSize[ 0 ][ 1 ]
        # Recuperation de la taille de la partition
        self.ptMountSize = self.ptMountSize[ 0 ][ 0]

        if( self.ptMountSize == -1 ):
            self.Debug( 1, "Impossible to compute filesystem size" )
            return False
        self.Debug( 5, "Mounting point size: " + self.ptMount  + " -> " + str( self.ptMountSize ) )

        # Recuperation de la taille de la partition hote du fichier de sauvegarde
        size = self.GetPtWithSize( None, os.path.dirname( os.path.realpath( self.fileName ) ) )
        size = size[ 0 ][ 0 ]
        self.Debug( 5, "Backup partition size: " + str( size ) )

        # Attention, si la taille de la partition de la sauvegarde est trop petite
        if( self.ptMountSize > size ):
            self.Debug( 1, "Insufficient disk space: " + str( size ) + " for " + str( self.ptMountSize ) )
            return False

        # ajout d'affichage supplementaire de la commande tar si le debug est suffisament important
        option = ""
        if( self.debug >= 4 ):
            option += "v"

        # Choix de la commande s'il faut faire un backup ou une restauration, choix du texte a afficher dans la barre de progression
        if( type == "backup" ):
            option += "c"
            text = _( "Creation" )
        elif( type == "restore" ):
            option += "x"
            text = _( "Restoration" )

        # Si le processus precedent n'a pas ete lance ou n'est pas fini (ex : poll = None), on attend
        if( self.procBackup == None or self.procBackup.poll() != None ):
            # -u pour creer ou mettre a jour une archive
            # -f pour preciser le nom de l'archive plutot que sur le stdout
            # Execution de la commande seuleument si l'on veut, sinon affichage de ce que l'on aurait fait
            if( self.noExec == False ):
                cmd = "cd '" + self.ptMount + "'; tar -" + option + "f \"" + self.fileName + "\" ."
            else:
                cmd = "cd '" + self.ptMount + "'; echo tar -" + option + "f \"" + self.fileName + "\" ."
            self.Debug( 5, "Launching command: " + cmd )
            self.procBackup = subprocess.Popen( cmd, shell=True )

            # verification de la fin du processus
            if( self.procBackup.poll() != None ):
                # Si l'on est pas en mode script, on affiche un popup de fin de processus
                if( self.noGui == False ):
                    self.Popup( text + _( " completed" ) )
                self.Debug( 5, text + " completed" )

            # Lancement de la barre de progression
            self.Debug( 5, "Launching the test of " + text + " of archive each second" )
            # Supression du tempo avant sa re-utilisation
            if( self.tempo != None ):
                gobject.source_remove( self.tempo )
            # Saut de ligne pour etre sur d'afficher correctement la barre de progression
            sys.stdout.write( "\n" )
            sys.stdout.flush()
            # Creation d'un timeout toutes les n ms, lancement de la fonction self.Progress avec ces parametres
            self.tempo = gobject.timeout_add( self.tempoDelay, self.Progress, 100, 100,
                            text + " of archive", self._BackupRestoreGPSEnd, text )

            return False

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de calcul et de mise en forme des temps estimes restant, total et du temps passe
    def GetTimeDelay( self, percent ):

        # Calcul du temps passe (en secondes) depuis le lancement de la sauvegarde
        secondsPass = gobject.get_current_time() - self.tempoStartTime
        # Calcul du temps estime total (en secondes) - en supposant que le temps passe est lineaire par rapport au travail effectue
        #      pour le tar, ce n'est pas le cas, rapide jusqu'a 11%, puis apparement lineaire, tres proche a partir de 40% - 37mn pour 1,6Go
        #      pour le bzip2, on l'est quasiment, à 2% on est tres proche - 22mn pour 1,6Go compresse en 1,5Go soit 98% - inutile !!!
        #      pour le bunzip2, il faut 8mn
        secondsTot = secondsPass / percent
        # Calcul du temps estime restant (en secondes)
        secondsRemind = secondsTot - secondsPass

        # Calcul du nombre d'heures passe (pour l'affichage)
        hoursPass = str( int( secondsPass / 3600 ) )
        # Calcul du nombre de minutes estimees au total, sans les heures calculees auparavant (pour l'affichage)
        minutesPass = str( int( ( secondsPass / 60 ) % 60 ) )
        # Calcul du nombre de secondes estimees au total, sans les heures et les minutes calculees auparavant (pour l'affichage)
        secondsPass = str( int( secondsPass % 60 ) )

        # Calcul du nombre d'heures estimees au total (pour l'affichage)
        hoursTot = str( int( secondsTot / 3600 ) )
        # Calcul du nombre de minutes estimees au total, sans les heures calculees auparavant (pour l'affichage)
        minutesTot = str( int( ( secondsTot / 60 ) % 60 ) )
        # Calcul du nombre de secondes estimees au total, sans les heures et les minutes calculees auparavant (pour l'affichage)
        secondsTot = str( int( secondsTot % 60 ) )

        # Calcul du nombre d'heures estimees restantes (pour l'affichage)
        hoursRemind = str( int( secondsRemind / 3600 ) )
        # Calcul du nombre de minutes estimees restantes, sans les heures calculees auparavant (pour l'affichage)
        minutesRemind = str( int( ( secondsRemind / 60 ) % 60 ) )
        # Calcul du nombre de secondes estimees restantes, sans les heures et les minutes calculees auparavant (pour l'affichage)
        secondsRemind = str( int( secondsRemind % 60 ) )

        # Mise en place de l'affichage du temps a afficher, en fonction des options fournies
        timeToPrint = ""
        if( self.configTimePassed == True ):
            timeToPrint += hoursPass + ":" + minutesPass + ":" + secondsPass + " -> "
        if( self.configTimeRemind == True ):
            timeToPrint += hoursRemind + ":" + minutesRemind + ":" + secondsRemind
        if( self.configTimeTot == True ):
            timeToPrint += " / " + hoursTot + ":" + minutesTot + ":" + secondsTot

        # Renvoi du texte a afficher
        return timeToPrint

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction de validation du processus apres sa fin
    def _BackupRestoreGPSEnd( self, type ):

        # Test de la valeur retournee pour valider ou non la tache finie
        if( self.procBackup.poll() != 0 ):
            type += _( " failed" )
        else:
            type += _( " completed" )

        self.Debug( 1, type + ": " + str( self.procBackup.poll() ) )

        # Si l'on est pas en mode script, on re-active les boutons de lancement des taches
        if( self.noGui == False ):
            # Recherche du bouton btnSave
            obj = self.SearchObj( "notebook.frameSaveRestore.boxSaveRestore.btnSave" )
            if( obj != None ):
                # Activation du bouton (de-sactive auparavant)
                obj.set_sensitive( True )
            obj = self.SearchObj( "notebook.frameSaveRestore.boxSaveRestore.btnRestore" )
            if( obj != None ):
                obj.set_sensitive( True )
            # Affichage du resultat par un popup
            self.Popup( type )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction d'affichage de la barre de progression
    def Progress( self, percentMin, percentMax, text, functEnd, paramEnd ):

        # TODO : possibilite de mettre en pause
        # La premiere fois que la fonction est lancee, l'application a deja ete lancee il y a self.tempoDelay secondes
        if( self.tempoStartTime == None ):
            self.tempoStartTime = gobject.get_current_time() - self.tempoDelay

        # Si le processus est fini
        if( self.procBackup.poll() != None ):

            # Recuperation du temps a afficher, etant arrive a 1, soit 100% (le processus est fini)
            timeToPrint = self.GetTimeDelay( 1 )
            # Creation du texte de la barre de progression
            text = '%s : 100%% - %s' % ( text, timeToPrint )
            # Taille de la barre en mode texte
            try:
                barSize = struct.unpack( "HH", fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, struct.pack( "HH", 0, 0 ) ) )[ 1 ] - len( text ) - 5
            except:
                barSize = 120

            # Affichage de la barre de progression en mode texte
            out = '\r [%s] %s\n' % ( '=' * barSize, text )
            sys.stdout.write( out )
            sys.stdout.flush()

            # Si l'on est en mode graphique
            if( self.noGui == False ):
                # Centrage du texte sur une taille de self.progressionBarSize (permettant d'avoir une barre de progression toujours a la meme taille
                textToPrint = text.center( self.progressionBarSize )
                # Affichage de la barre de progression (la valeur doit etre inferieure ou egale a 1
                self.progressionBar.set_fraction( 1 )
                # Affichage du texte sur la barre de progression
                self.progressionBar.set_text( textToPrint )

            # Lancement de la fonction de validation du processus
            functEnd( paramEnd )

            # Suppression du minuteur et de la date de debut du processus
            gobject.source_remove( self.tempo )
            self.tempo = None
            self.tempoStartTime = None

            # Si on a deja voulu quitter, on quitte a la fin du processus
            if( self.quit == True ):
                self.Debug( 5, "Exiting on request" )
                self.Delete( None )

            # Pour arreter le minuteur, il faut renvoyer False
            return False

        # Le processus n'est pas fini, il faut calculer et afficher la barre de progression
        # Initialisation du type de la nouvelle valeur, un nombre flottant a 2 valeurs apres la virgule
        newVal = round( float( 0.01 ), 2 )
        # Recuperation de la taille du fichier de destination
        newSize = os.path.getsize( self.fileName )
        self.Debug( 7, "File size: "  + self.fileName + " -> " + str( newSize ) + " / " + str( self.ptMountSize ) )

        # On estime que la taille du fichier finale sera percentMin, mais qu'au maximum le fichier aura une taille de percentMax
        # On calcul donc le pourcentage estime entre ces deux valeurs, avec des sauts de 10 pourcent
        for percent in range( percentMin, percentMax + 10, 10 ):
            # Si la taille du fichier est inferieur au pourcentage de la taille du fichier original, on calcule la nouvelle
            # valeur de la barre de progression comprise entre 0,00 et 1
            if( newSize <= self.ptMountSize * percent / 100 ):
                self.Debug( 7, "<" + str( percent ) )
                newVal = round( float( newSize / float( self.ptMountSize * percent / 100 ) ), 2 )
                break
            # Si toutefois on depasse le pourcentage maximum, la valeur restera a 1 (soit 100%)
            elif( percent > percentMax ):
                newVal = 1

        # Au depart, pas d'idees sur le temps restant, il vient au fur et a mesure
        timeToPrint = ""
        if( newVal >= 0.01 ):
            # Recuperation de l'affichage du temps estime restant, total et du temps passe
            timeToPrint = self.GetTimeDelay( newVal )

        # Remise sous la forme 100%, soit un entier compris entre 0 et 100
        newVal = int( 100 * newVal )
        # Presentation avec le texte, le pourcentage et le temps a afficher
        text = '%s : %3d %% - %8s' % ( text, newVal, timeToPrint )
        # Taille de la barre en mode texte
        try:
            barSize = struct.unpack( "HH", fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, struct.pack( "HH", 0, 0 ) ) )[ 1 ] - len( text ) - 5
        except:
            barSize = 120

        if( self.noGui == False ):
            # Ajustement de la taille de la progress barre à 120 caracteres avec centrage du texte
            textToPrint = text.center( self.progressionBarSize )
            # Affichage de la barre de progression (la valeur doit etre inferieure a 1)
            self.progressionBar.set_fraction( round( float( newVal ) / 100, 2 ) )
            # Affichage du texte sur la barre de progression
            self.progressionBar.set_text( textToPrint )

        # Pour l'affichage en mode texte, calcul de la valeur par rapport a la taille de la barre en mode texte
        newVal = newVal * barSize / 100
        # Affichage de la barre de progression
        out = '\r [%s%s] %s' % ( '=' * newVal, ' ' * ( barSize - newVal ), text )
        sys.stdout.write( out )
        sys.stdout.flush()

        # Pour continuer la barre de progression, il faut renvoyer la valeur True
        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction pour quitter l'application
    def Delete( self, widget, event = None ):

        # Afin de ne pas quitter sauvagement les processus en cours de sauvegarde ou de restauration, on ne quitte que si
        #     le processus est termine, il faut donc revenir, d'ou l'enregistrement de self.quit pour revenir a la fin du processus
        self.quit = True

        # Supression de la mise a jour automatique du combo de la liste des points de montage
        if( self.tempoCombo != None ):
            gobject.source_remove( self.tempoCombo )

        # On ne quitte que si le sous-processus est fini
        if( self.tempo != None ):
            self.Debug( 1, "Waiting for end of child process" )
            return False

        # Fermeture du fichier de log, si ce n'est pas stdout
        if( self.logFile != sys.stdout ):
            self.logFile.close()

        # Si l'on est pas en mode script, fermeture de gtk
        if not( self.noGui ):
            gtk.main_quit()
        # Sinon, sortie par le mode sys
        else:
            sys.exit( 0 )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de creation et d'affichage d'un onglet
    def CreateCustomTab( self, text, notebook, frame ):

        #On crée une eventbox
        eventBox = gtk.EventBox()
        #On crée une boite horizontale
        tabBox = gtk.HBox( False, 2 )
        #On crée un label "text" (text donné en attribut)
        tabLabel = gtk.Label( text )

        eventBox.show()
        tabLabel.show()
        #On attache tablabel
        tabBox.pack_start( tabLabel, False )

        tabBox.show_all()
        #On ajoute la boite à l'eventbox
        eventBox.add( tabBox )

        return eventBox


    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction d'affichage d'un popup
    def Popup( self, text ):

        # Creation d'un popup
        dialog = gtk.MessageDialog( None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, text )
        # Affichage du popup
        dialog.run()
        # Suppression du popup
        dialog.destroy()

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction d'affichage et de mise a jour du combo des points de montage
    def MakeCombo( self ):

        # Recuperation des points de montage potentiels
        self.GetPtMounts()

        # Creation du combo s'il n'existe pas
        if( self.ptCombo == None ):
            self.ptCombo = gtk.combo_box_new_text()
            # Affichage d'une ligne vide, afin de forcer le choix s'il n'a pas ete fait auparavant
            self.ptCombo.append_text( '' )

        # Recuperation des donnees du combo
        combo = self.ptCombo.get_model()

        # --------- Premiere etape, ajout des points de montage inexistants ---------

        # Pour chaque point de montage
        for ptMountSize, ptMount in self.ptMounts:
            # Par defaut on a pas trouve
            found = False
            # Pour chaque element du combo (on commence a 1 puisqu'on a un element vide)
            for i in range( 1, len( combo ), 1 ):
                # Si l'on trouve le point de montage, on arrete le parcours
                if( ptMount == combo[ i ][ 0 ] ):
                    found = True
                    break
            # Si l'on est arrive au bout du combo, on a pas trouve le point de montage
            if( found == False ):
                # On ajoute le point de montage
                self.ptCombo.append_text( str( ptMount ) )
                if( ptMount == self.ptMount ):
                    # Si le point de montage est enregistre, on selectionne ce point de montage dans le combo
                    self.ptCombo.set_active( len( combo ) - 1 )

        # --------- Deuxieme etape, supression des points de montage n'existant plus ---------
        # Pour chaque element du combo (on commence a 1 puisqu'on a un element vide)
        for i in range( 1, len( combo ), 1 ):
            # Par defaut, on a pas trouve l'element
            found = False
            # Pour chaque point de montage
            for ptMountSize, ptMount in self.ptMounts:
                # Si on trouve le point de montage
                if( ptMount == combo[ i ][ 0 ] ):
                    found = True
            # Si le point de montage n'a pas ete trouve, on le supprime
            if( found == False ):
                self.ptCombo.remove_text( i )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de mise a jour de la variable associee a chaque case a cocher pour l'affichage des temps restant, total, passe
    def UpdateConfigTime( self, widget ):

        # Recuperation du nom de la case a cocher
        name = widget.get_name()
        # Modification de la variable associee (meme nom)
        setattr( self, name, widget.get_active())

        return True

    #------------------------------------------ DEFINITION DES FONCTIONS D'AFFICHAGE ----------------------------------------
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de creation de la frame des options
    def FrameOption( self, notebook ):

        #--------------------------------------
        # Onglet OPTIONS
        #--------------------------------------
        frame = gtk.Frame( _( "Options" ) )
        frame.set_border_width( 10 )
        frame.set_name( "frameOptions" )
        frame.show()

        #On crée une boite verticale
        tabBox = gtk.HBox( False, 2 )
        tabBox.set_name( "frameOptions" )
        frame.add( tabBox )
        tabBox.show()

        #On crée une boite horizontale
        tabBoxLeft = gtk.VBox( False, 2 )
        tabBoxLeft.set_size_request ( 120, -1 )
        tabBox.add( tabBoxLeft )
        tabBoxLeft.show()
        #On crée une boite horizontale
        tabBoxRight = gtk.VBox( False, 2 )
        tabBoxRight.set_size_request ( 480, -1 )
        tabBox.add( tabBoxRight )
        tabBoxRight.show()

        # image
        image = gtk.Image()
        image.set_from_file( self.dirPix + "options.png" )
        tabBoxLeft.pack_start( image, True, False, 2 )

        label = gtk.Label( _( "Please indicate the mounting point of your Tomtom:" ) )
        label.set_justify( gtk.JUSTIFY_CENTER )
        tabBoxRight.pack_start( label, True, False, 2 )

        # bouton parcourir
#        p = gtk.Button( _( "Sélectionner le point de montage du TomTom..." ) )
#      tabBox.pack_start( p, True, False, 2 )
#        p.connect( "clicked", self.parcourir_gps )

        # Liste des points de montage possibles
        self.MakeCombo()
        tabBoxRight.pack_start( self.ptCombo, True, False, 0 )
        # Lancement de la mise a jour automatiquement toutes les 2 secondes
        self.tempoCombo = gobject.timeout_add( 2000, self.MakeCombo )

        # separator
        hs = gtk.HSeparator()
        tabBoxRight.pack_start( hs, False, False, 2 )

        # Liste des modeles
        self.modeleCombo = gtk.combo_box_new_text()
        i = 0
        for text in self.models:
            self.modeleCombo.append_text( str( text ) )
            if( text == self.model ):
                self.modeleCombo.set_active( i )
            i += 1
        #self.modeleCombo.connect( 'changed', self.OnUpdate )
        tabBoxRight.pack_start( self.modeleCombo, True, False, 0 )

        hs = gtk.HSeparator()
        tabBoxRight.pack_start( hs, False, False, 2 )

        label = gtk.Label( _( "During backup or restore, display:" ) )
        label.set_justify( gtk.JUSTIFY_CENTER )
        tabBoxRight.pack_start( label, True, False, 2 )

        # Case a cocher pour l'affichage du temps passe dans la barre de progression
        button = gtk.CheckButton( _( "elapsed time" ), False )
        button.set_name( "configTimePassed" )
        button.connect( "clicked", self.UpdateConfigTime )
        if( self.configTimePassed == True ):
            button.set_active( True )
        tabBoxRight.pack_start( button, True, False, 0 )

        # Case a cocher pour l'affichage du temps estime restant dans la barre de progression
        button = gtk.CheckButton( _( "remaining time" ), False )
        button.set_name( "configTimeRemind" )
        button.connect( "clicked", self.UpdateConfigTime )
        if( self.configTimeRemind == True ):
            button.set_active( True )
        tabBoxRight.pack_start( button, True, False, 0 )

        # Case a cocher pour l'affichage du temps estime total dans la barre de progression
        button = gtk.CheckButton( _( "total time" ), False )
        button.set_name( "configTimeTot" )
        button.connect( "clicked", self.UpdateConfigTime )
        if( self.configTimeTot == True ):
            button.set_active( True )
        tabBoxRight.pack_start( button, True, False, 0 )

        # separator
        hs = gtk.HSeparator()
        tabBoxRight.pack_start( hs, True, False, 2 )

        button = gtk.Button( stock = gtk.STOCK_SAVE )
        tabBoxRight.pack_start( button, True, False, 0 )

        # Connexion du signal "clicked" du GtkButton
        button.connect( "clicked", self.OnUpdate )

        eventBox = self.CreateCustomTab( _( "Options" ), notebook, frame )
        notebook.append_page( frame, eventBox )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de creation de la frame du GPSFix
    def FrameGPSQuickFix( self, notebook ):

        #--------------------------------------
        # Onglet GPSQuickFix
        #--------------------------------------
        frame = gtk.Frame( _( "GPSQuickFix" ) )
        frame.set_border_width( 10 )
        frame.set_name( "frameGPSQuickFix" )
        frame.show()

        #On crée une boite verticale
        tabBox = gtk.HBox( False, 2 )
        tabBox.set_name( "boxGPSQuickFix" )
        frame.add( tabBox )
        tabBox.show()

        #On crée une boite horizontale
        tabBoxLeft = gtk.VBox( False, 2 )
        tabBoxLeft.set_size_request ( 120, -1 )
        tabBox.add( tabBoxLeft )
        tabBoxLeft.show()
        #On crée une boite horizontale
        tabBoxRight = gtk.VBox( False, 2 )
        tabBoxRight.set_size_request ( 480, -1 )
        tabBox.add( tabBoxRight )
        tabBoxRight.show()

        # image
        image = gtk.Image()
        image.set_from_file( self.dirPix + "gpsquickfix.png" )
        tabBoxLeft.pack_start( image, True, False, 2 )

        # label
        label = gtk.Label( _( "This update sets the last known positions of the satellites. \n\nIt allows your GPS to find its initial position in less than 30 seconds \nand to initiate navigation more quickly... \n\nPlease ensure that you have properly set your GPS parameters \nin the options." ) )
        # On centre le texte
        label.set_justify( gtk.JUSTIFY_CENTER )
        tabBoxRight.pack_start( label, True, False, 2 )

        # bouton maj quickfix
        if( self.couldGpsFix ):
            btn_csi = gtk.Button( _( "Start GPSQuickfix update" ) )
            tabBoxRight.pack_start( btn_csi, True, False, 2 )
            # On connecte le signal "clicked" du bouton a la fonction qui lui correspond
            btn_csi.connect( "clicked", self.GpsQuickFix )
        else:
            btn_csi = gtk.Button( _( "Cannot start GPSQuickfix update (cabextract is missing)" ) )
            btn_csi.set_sensitive( False )
            tabBoxRight.pack_start( btn_csi, True, False, 2 )
            # On ne connecte à aucune fonction

        eventBox = self.CreateCustomTab( _( "GPSQuickFix" ), notebook, frame )
        notebook.append_page( frame, eventBox )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de creation de la frame de lancement du backup et de la restauration
    def FrameBackupRestore( self, notebook ):

        #---------------------------------------------------------------------
        # Onglet SAUVEGARDE ET RESTAURATION
        #---------------------------------------------------------------------

        frame = gtk.Frame( _( "Backup and restore" ) )
        frame.set_border_width( 10 )
        frame.set_name( "frameSaveRestore" )
        frame.show()

        #On crée une boite verticale
        tabBox = gtk.HBox( False, 2 )
        tabBox.set_name( "boxSaveRestore" )
        frame.add( tabBox )
        tabBox.show()

        #On crée une boite horizontale
        tabBoxLeft = gtk.VBox( False, 2 )
        tabBoxLeft.set_size_request ( 120, -1 )
        tabBox.add( tabBoxLeft )
        tabBoxLeft.show()
        #On crée une boite horizontale
        tabBoxRight = gtk.VBox( False, 2 )
        tabBoxRight.set_size_request ( 480, -1 )
        tabBox.add( tabBoxRight )
        tabBoxRight.show()

        # image
        image = gtk.Image()
        image.set_from_file( self.dirPix + "saverestore.png" )
        tabBoxLeft.pack_start( image, True, False, 2 )

        # Text pour le choix du fichier de sauvegarde
        label = gtk.Label( _( "Backup file:" ) )
        label.set_justify( gtk.JUSTIFY_CENTER )
        tabBoxRight.pack_start( label, True, False, 2 )

        # TODO : n'afficher que le nom du fichier, pas le chemin complet
        # Liste des fichiers de sauvegarde existant et un nouveau
        self.saveFileCombo = gtk.combo_box_new_text()
        # recuperation du nom d'un fichier
        file = self.GetNewFileName()
        # Si le fichier existe, recuperation d'un nom presque certainement inexistant
        if( os.path.exists( file ) ):
            file = self.GetNewFileName( True )

        # Creation d'un combo contenant la liste des fichiers de sauvegarde
        # Ajout du nom de fichier nouveau (si l'on veut en creer un nouveau)
        self.saveFileCombo.append_text( file )
        # Ajout d'une ligne vide
        self.saveFileCombo.append_text( "----------------" )

        # Si le nom du fichier a ete fourni, ajout du nom du fichier, et selection du fichier dans le combo
        if( self.fileName != False ):
            self.saveFileCombo.append_text( os.path.realpath( self.fileName ) )
            self.saveFileCombo.set_active( 2 )
        # Sinon selection du nouveau fichier
        else:
            self.saveFileCombo.set_active( 0 )

        # Verification ou creation du dossier backup
        if not( os.path.exists( self.dirBackup ) ):
            os.mkdir( self.dirBackup )
        # importation des anciennes sauvegardes (pytomtom =< 0.4)
        # Ouverture de l ancien dossier de sauvegarde
        oldfiles = os.listdir( self.dir )
        for file in oldfiles:
            f, extension = os.path.splitext( file )
            if( extension == ".tar" and ( self.fileName == False or os.path.realpath( self.dir + "/" + file ) != os.path.realpath( self.fileName ) ) ):
                # on copie les anciennes sauvegardes dans le nouveau rep backup
                shutil.move( self.dir + "/" + file, self.dirBackup + "/" + file )

        # Ajout de tous les anciens fichiers de sauvegarde
        # Ouverture du dossier de sauvegarde
        #files = os.listdir( self.dir )
        files = os.listdir( self.dirBackup )
        # Pour chaque fichier
        for file in files:
            # Recuperation de l'extension du fichier pour savoir s'il s'agit d'une sauvegarde
            f, extension = os.path.splitext( file )
            # Ajout du fichier de sauvegarde, s'il s'agit d'une sauvegarde, et qu'il ne s'agit pas du fichier fourni en option
            #if( extension == ".tar" and ( self.fileName == False or os.path.realpath( self.dir + "/" + file ) != os.path.realpath( self.fileName ) ) ):
            if( extension == ".tar" and ( self.fileName == False or os.path.realpath( self.dirBackup + "/" + file ) != os.path.realpath( self.fileName ) ) ):
                self.saveFileCombo.append_text( self.dirBackup + "/" + file )

        #self.saveFileCombo.set_size_request ( 60, -1 )
        tabBoxRight.pack_start( self.saveFileCombo, True, False, 0 )

        # Mise en place de la barre de progression
        self.progressionBar = gtk.ProgressBar()

        # Affichage du texte dans la barre de progression pour avoir une taille precise de la barre
        text = "";
        self.progressionBar.set_text( text.center( self.progressionBarSize ) )
        align = gtk.Alignment( 0.5, 0.5, 0, 0 )
        tabBoxRight.pack_start( align, False, False, 10 )
        align.show()
        align.add( self.progressionBar )
        self.progressionBar.show()

        # Affichage d'information de la duree
        label = gtk.Label( _( "In order to complete these operations " ) + App + _( " takes time \nand consumes disk space. \nFor information, 25 minutes and 1GB on disk for a One Series 30" ) )
        label.set_justify( gtk.JUSTIFY_CENTER )
        tabBoxRight.pack_start( label, True, False, 2 )

        # separator
        hs = gtk.HSeparator()
        tabBoxRight.pack_start( hs, True, False, 2 )

        # bouton sauvegarde
        # Si la commande tar n'existe pas, la sauvegarde ne peut etre lancee, l'affichage change et le bouton ne peut
        #     etre clique
        if( self.couldBackup ):
            btnSave = gtk.Button( _( "Start backup..." ) )
            btnSave.props.name = "btnSave"
            tabBoxRight.pack_start( btnSave, True, False, 2 )
            # On connecte le signal "clicked" du bouton a la fonction qui lui correspond
            btnSave.connect( "clicked", self.BackupRestoreGPS, "backup" )
        else:
            btnSave = gtk.Button( _( "Cannot start backup (tar is missing)" ) )
            btnSave.set_sensitive( False )
            btnSave.props.name = "btnSave"
            tabBoxRight.pack_start( btnSave, True, False, 2 )
            # On connecte le signal "clicked" du bouton a rien

        # separator
        hs = gtk.HSeparator()
        tabBoxRight.pack_start( hs, True, False, 2 )

        # bouton RESTAURATION
        # Si la commande tar n'existe pas, la sauvegarde ne peut etre lancee, l'affichage change et le bouton ne peut
        #     etre clique
        if( self.couldBackup ):
            btnRestore = gtk.Button( _( "Start restore..." ) )
            btnRestore.set_name( "btnRestore" )
            tabBoxRight.pack_start( btnRestore, True, False, 2 )
            # On connecte le signal "clicked" du bouton a la fonction qui lui correspond
            btnRestore.connect( "clicked", self.BackupRestoreGPS, "restore" )
        else:
            btnRestore = gtk.Button( _( "Cannot start restore (tar is missing)" ) )
            btnRestore.set_sensitive( False )
            btnRestore.set_name( "btnRestore" )
            tabBoxRight.pack_start( btnRestore, True, False, 2 )
            # On connecte le signal "clicked" du bouton a rien

        label = gtk.Label( _( "Please use restore only in case of necessity !" ) )
        label.set_justify( gtk.JUSTIFY_CENTER )
        tabBoxRight.pack_start( label, True, False, 2 )

        # Creation et affichage de la frame
        eventBox = self.CreateCustomTab( _( "Backup and Restore" ), notebook, frame )
        notebook.append_page( frame, eventBox )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de creation de la frame POI
    def FramePoi( self, notebook ):

        #--------------------------------------
        # Onglet POI
        #--------------------------------------
        frame = gtk.Frame( _( "POI" ) )
        frame.set_border_width( 10 )
        frame.set_name( "framePoi" )
        frame.show()
        #On crée une boite verticale
        tabBox = gtk.HBox( False, 2 )
        tabBox.set_name( "boxPoi" )
        frame.add( tabBox )
        tabBox.show()

        #On crée une boite horizontale
        tabBoxLeft = gtk.VBox( False, 2 )
        tabBoxLeft.set_name( "tabBoxLeftPoi" )
        tabBoxLeft.set_size_request ( 120, -1 )
        tabBox.add( tabBoxLeft )
        tabBoxLeft.show()
        #On crée une boite horizontale
        tabBoxRight = gtk.VBox( False, 2 )
        tabBoxRight.set_name( "tabBoxRightPoi" )
        tabBoxRight.set_size_request ( 480, -1 )
        tabBox.add( tabBoxRight )
        tabBoxRight.show()

        # image
        image = gtk.Image()
        image.set_from_file( self.dirPix + "poi.png" )
        tabBoxLeft.pack_start( image, True, False, 2 )

        labelfirststep = gtk.Label( _( "First, you have to add POI to pyTOMTOM's database") )
        labelfirststep.set_justify( gtk.JUSTIFY_CENTER )
        tabBoxRight.pack_start( labelfirststep, True, False, 2 )

        # bouton
        btndbAddPoi = gtk.Button( _( "Add POI (.ov2) to database..." ) )
        tabBoxRight.pack_start( btndbAddPoi, True, False, 2 )
        btndbAddPoi.connect( "clicked", self.addPoiToDatabase )

        # separator
        hs = gtk.HSeparator()
        tabBoxRight.pack_start( hs, True, False, 2 )

        labelsteptwo = gtk.Label( _( "Now, you can easily add or remove it from GPS...") )
        labelsteptwo.set_justify( gtk.JUSTIFY_CENTER )
        tabBoxRight.pack_start( labelsteptwo, True, False, 2 )

        # Liste des poi de la base
        self.poiCombo = gtk.combo_box_new_text()
        self.poiCombo.set_name( "poiCombo" )
        # Ajout d'une ligne vide
        self.poiCombo.append_text( _( "Select POI in database" ) )
        self.poiCombo.append_text( "----------------------" )
        # selection par defaut
        self.poiCombo.set_active( 0 )

        # Ajout de tous les anciens poi
        if( os.path.exists( self.dirPoi ) ):
            # Ouverture du dossier des poi
            files = os.listdir( self.dirPoi )
            #print files
            # On tri par ordre alphabetique
            files.sort()
            # Pour chaque fichier
            for file in files:
                # Recuperation de l'extension du fichier pour savoir s'il s'agit d'un poi
                #f, extension = os.path.splitext( file )
                # Ajout du fichier poi, s'il s'agit d'un poi, et qu'il ne s'agit pas du fichier fourni en option
                #if( extension == ".ov2" ):
                #      self.poiCombo.append_text( f )
                self.poiCombo.append_text( file )
        tabBoxRight.pack_start( self.poiCombo, True, False, 0 )

        if( self.CurrentMap != False ):
            labelmap = gtk.Label(  _( "Selected map: " ) + self.CurrentMap )
            tabBoxRight.pack_start( labelmap, True, False, 2 )
        btnAddPoi = gtk.Button( _( "Add seleted POI on TomTom" ) )
        if( self.CurrentMap == False ):
            btnAddPoi.set_sensitive( False )
        tabBoxRight.pack_start( btnAddPoi, True, False, 2 )
        btnAddPoi.connect( "clicked", self.addPoiToTomtom )
        btnDelPoi = gtk.Button( _( "Delete seleted POI from TomTom" ) )
        if( self.CurrentMap == False ):
            btnDelPoi.set_sensitive( False )
        tabBoxRight.pack_start( btnDelPoi, True, False, 2 )
        btnDelPoi.connect( "clicked", self.delPoiOnTomtom )

        btndbDelPoi = gtk.Button( _( "Delete POI from database..." ) )
        #btndbDelPoi.set_sensitive( False )
        tabBoxRight.pack_start( btndbDelPoi, True, False, 2 )
        btndbDelPoi.connect( "clicked", self.delPoiFromDatabase )

        eventBox = self.CreateCustomTab( _( "POI" ), notebook, frame )
        notebook.append_page( frame, eventBox )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de creation de la frame PERSONNALISER
    def FramePersonalize( self, notebook ):

        #--------------------------------------
        # Onglet PERSONNALISER
        #--------------------------------------
        frame = gtk.Frame( _( "Personalize" ) )
        frame.set_border_width( 10 )
        frame.set_name( "Personalize" )
        frame.show()
        #On crée une boite verticale
        tabBox = gtk.HBox( False, 2 )
        tabBox.set_name( "boxPersonalize" )
        frame.add( tabBox )
        tabBox.show()

        #On crée une boite horizontale
        tabBoxLeft = gtk.VBox( False, 2 )
        tabBoxLeft.set_size_request ( 120, -1 )
        tabBox.add( tabBoxLeft )
        tabBoxLeft.show()
        #On crée une boite horizontale
        tabBoxRight = gtk.VBox( False, 2 )
        tabBoxRight.set_size_request ( 480, -1 )
        tabBox.add( tabBoxRight )
        tabBoxRight.show()

        # image
        image = gtk.Image()
        image.set_from_file( self.dirPix + "personalize.png" )
        tabBoxLeft.pack_start( image, True, False, 2 )

        # label
        label = gtk.Label( _( "Replace the startup screen of your GPS by the picture of your choice" ) )
        tabBoxRight.pack_start( label, True, False, 2 )
        #TODO verifier presence ImageMagick
        # subprocess.call( [ "convert image.jpg -resize 320x240 -background black -gravity center -extent 320x240 splash.bmp" ], shell = True )
        # bouton
        b = gtk.Button( _( "Select image..." ) )
        tabBoxRight.pack_start( b, True, False, 2 )
        b.connect( "clicked", self.selectImg )

        eventBox = self.CreateCustomTab( _( "Personalize" ), notebook, frame )

        notebook.append_page( frame, eventBox )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de creation de la frame a propos
    def FrameAbout( self, notebook ):

        #--------------------------------------
        # Onglet A PROPOS
        #--------------------------------------
        frame = gtk.Frame( _( "About" ) )
        frame.set_border_width( 10 )
        frame.set_name( "frameAbout" )
        frame.show()

        #On crée une boite horizontale
        tabBox = gtk.VBox( False, 2 )
        tabBox.set_name( "boxAbout" )
        frame.add( tabBox )
        tabBox.show()

        # image
        image = gtk.Image()
        image.set_from_file( self.dirPix + "pytomtom.png" )
        tabBox.pack_start( image, True, False, 2 )

        #On crée un label "text" (text donné en attribut)
        tabLabel = gtk.Label( _( "version " ) + Ver )
        tabLabel.set_justify( gtk.JUSTIFY_CENTER )
        tabBox.pack_start( tabLabel, True, False, 2 )

        #self.LatestRelease()
        # bouton LatestRelease()
        btnLatest = gtk.Button(  _( "Need to update ?" ) )
        tabBox.pack_start( btnLatest, True, False, 2 )
        btnLatest.connect( "clicked", self.LatestRelease )

        # bouton acces au site web
        btnWeb = gtk.Button( WebUrl )
        tabBox.pack_start( btnWeb, True, False, 2 )
        btnWeb.connect( "clicked", self.WebConnect )
        btnWeb.set_tooltip_text( _( "Visit homepage..." ) )

        eventBox = self.CreateCustomTab( _( "About" ), notebook, frame )
        notebook.append_page( frame, eventBox )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de creation de la frame quit
    def FrameQuit( self, notebook ):

        #--------------------------------------
        # Onglet QUITTER
        #--------------------------------------
        frame = gtk.Frame( _( "Exit" ) )
        frame.set_border_width( 10 )
        frame.set_name( "frameQuit" )
        frame.show()

        #On crée une boite verticale
        tabBox = gtk.HBox( False, 2 )
        tabBox.set_name( "boxQuit" )
        frame.add( tabBox )
        tabBox.show()

        #On crée une boite horizontale
        tabBoxLeft = gtk.VBox( False, 2 )
        tabBoxLeft.set_size_request ( 120, -1 )
        tabBox.add( tabBoxLeft )
        tabBoxLeft.show()
        #On crée une boite horizontale
        tabBoxRight = gtk.VBox( False, 2 )
        tabBoxRight.set_size_request ( 480, -1 )
        tabBox.add( tabBoxRight )
        tabBoxRight.show()

        # image
        image = gtk.Image()
        image.set_from_file( self.dirPix + "quit.png" )
        tabBoxLeft.pack_start( image, True, False, 2 )

        # label
        label = gtk.Label( _( "Don't forget to cleanly unmount your TomTom!" ) )
        tabBoxRight.pack_start( label, True, False, 2 )

        # demontage propre du GPS
        btnUnmount = gtk.Button( _( "Unmount" ) )
        #TODO: griser le btn si gps pas branche
        if( self.boxInit == 0 ):
            btnUnmount.set_sensitive( False )
        tabBoxRight.pack_start( btnUnmount, True, False, 2 )
        btnUnmount.connect( "clicked", self.UMount )

        # bouton quitter
        btnQuit = gtk.Button( stock = gtk.STOCK_QUIT )
        tabBoxRight.pack_start( btnQuit, True, False, 2 )
        btnQuit.connect( "clicked", self.Delete )
        btnQuit.set_tooltip_text( _( "bye bye !" ) )

        eventBox = self.CreateCustomTab( _( "Exit" ), notebook, frame )
        notebook.append_page( frame, eventBox )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction parcourir pour selectionner un dossier / conservation en cas de besoin def parcourir_gps( self,entry ):
    def selectFolder( self,entry ):

        self.popup = gtk.FileChooserDialog( _( "Open..." ), gtk.Window( gtk.WINDOW_TOPLEVEL ),
                gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, ( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK ) );

        if( self.popup.run() == gtk.RESPONSE_OK ):
            dossier = self.popup.get_filename()
            self.Debug( 5, dossier )
            #self.labelfolder.set_text( dossier )
            self.popup.destroy()

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction parcourir pour selectionner un fichier gtk.FILE_CHOOSER_ACTION_OPEN
    def selectImg( self,entry ):

        self.popup = gtk.FileChooserDialog( _( "Open folder..." ), gtk.Window( gtk.WINDOW_TOPLEVEL ),
                gtk.FILE_CHOOSER_ACTION_OPEN, ( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK ) );
        filter = gtk.FileFilter()
        filter.set_name( "images" )
        filter.add_pattern( "*.jpg" )
        filter.add_pattern( "*.png" )
        self.popup.add_filter( filter )
        repHome = os.getenv( "HOME" )
        self.popup.set_current_folder( repHome )

        if( self.popup.run() == gtk.RESPONSE_OK ):
            imgSelected = self.popup.get_filename()
            self.Debug( 5, imgSelected )
            self.popup.destroy()
            # Verification de l'existence du fichier splash ou splashw.bmp
            if( os.path.exists( self.ptMount + "/splashw.bmp" ) ):
                cmd = ("convert '" + imgSelected + "' -resize 480x272 -background black -gravity center -extent 480x272 '"+ self.ptMount + "/splashw.bmp'")
                p = subprocess.Popen( cmd, shell=True )
                p.wait()
                self.Popup( _( "OK" ) )
                return True
            else:
                if( os.path.exists( self.ptMount + "/splash.bmp" ) ):
                    cmd = ("convert '" + imgSelected + "' -resize 320x240 -background black -gravity center -extent 320x240 '"+ self.ptMount + "/splash.bmp'")
                    p = subprocess.Popen( cmd, shell=True )
                    p.wait()
                    self.Popup( _( "OK" ) )
                    return True
                else:
                    self.Popup( _( "Error" ) )
                    return True

        #self.popup.destroy()
        #self.Popup( _( "OK" ) )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction parcourir pour selectionner un fichier gtk.FILE_CHOOSER_ACTION_OPEN
    def addPoiToDatabase( self,entry ):

        self.popup = gtk.FileChooserDialog( _( "Open folder..." ), gtk.Window( gtk.WINDOW_TOPLEVEL ),
                gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, ( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK ) );
        filter = gtk.FileFilter()
        filter.set_name( "POI (*.ov2)" )
        filter.add_pattern( "*.ov2" )
        self.popup.add_filter( filter )
        repHome = os.getenv( "HOME" )
        self.popup.set_current_folder( repHome )

        if not( os.path.exists( self.dirPoi ) ):
            # Creation du repertoire si inexistant
            os.mkdir( self.dirPoi )

        if( self.popup.run() == gtk.RESPONSE_OK ):
            dirSelected = self.popup.get_filename()
            self.Debug( 5, dirSelected )
            # on recupere juste le nom du repertoire qui servira a nommer le poi
            ( filepath, filename ) = os.path.split( dirSelected )
            # on cree le rep du poi dans la base
            cmd = ("mkdir -p '" + self.dirPoi + filename + "'" )
            p = subprocess.Popen( cmd, shell=True )
            p.wait()
            # on y copie les fichiers
            cmd = ("cp '" + dirSelected + "/'* '" + self.dirPoi + filename + "/'" )
            p = subprocess.Popen( cmd, shell=True )
            p.wait()
            # on rajoute la nouvelle entree a la liste
            self.poiCombo.append_text( filename )

        self.popup.destroy()
        self.Popup( _( "POI added to database" ) )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction copie du poi sur le tomtom
    def addPoiToTomtom( self,entry ):

        selectedPoi = self.poiCombo.get_active_text()
        cmd = ("cp '" + self.dirPoi + selectedPoi + "/'* '" + self.ptMount + "'/" + self.CurrentMap )
        p = subprocess.Popen( cmd, shell=True )
        p.wait()
        self.Popup( _( "POI " ) + selectedPoi + _( " added to TomTom" ) )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction suppression du poi sur le tomtom
    def delPoiOnTomtom( self,entry ):

        selectedPoi = self.poiCombo.get_active_text()
        files = os.listdir( self.dirPoi + selectedPoi )
        for file in files:
            cmd = ("rm -f '" + self.ptMount + "'/" + self.CurrentMap + "/'" + file + "'")
            p = subprocess.Popen( cmd, shell=True )
            p.wait()

        self.Popup( _( "POI " ) + selectedPoi + _( " deleted from TomTom" ) )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction suppression du poi sur le tomtom
    def delPoiFromDatabase( self,entry ):
        # on supprime  les fichiers
        selectedPoi = self.poiCombo.get_active_text()
        cmd = ("rm -rf '" + self.dirPoi + selectedPoi + "'")
        #print cmd
        p = subprocess.Popen( cmd, shell=True )
        p.wait()
        # on supprime l'entree dans le menu deroulant
        indexPoi = self.poiCombo.get_active()
        self.poiCombo.remove_text( indexPoi )

        self.Popup( _( "POI " ) + selectedPoi + _( " deleted from database" ) )

        return True

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # fonction test en fond de tache   NON UTILISEE
    def ma_fonction( self ):
        #print "toto"
        if( self.ptMount != False ):
            gpsStatus = "connected"
            print gpsStatus
        else:
            gpsStatus = "disconnected"
        #while True:
            #self.ma_fonction()
        return True


    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Fonction de demarrage de la classe
    def __init__( self ):

        # recuperation de pyTOMTOM en pytomtom (=<0.4.2)
        #self.Recup()
        # Recuperation de la configuration
        self.GetConfig()

        # Si on est pas en mode script
        if( self.noGui == False ):
            #On cree la fenetre principale
            self.window = gtk.Window( gtk.WINDOW_TOPLEVEL )
            # En cas de fermeture de la fenetre, on appel la fonction Delete
            self.window.connect( "delete_event", self.Delete )
            self.window.set_border_width( 10 )
            self.window.set_title( App )
            self.window.set_icon_from_file( self.dirPix + "icon.png" )
            # centrage de la fenetre
            self.window.set_position( gtk.WIN_POS_CENTER )
            # timeout for tooltips
            settings = self.window.get_settings()
            settings.set_property( 'gtk-tooltip-timeout', 0 )

            #*************************************************************************************************************
            #On cree un nouveau notebook
            notebook = gtk.Notebook()
            notebook.set_name( "notebook" )
            self.window.add( notebook )
            notebook.show()
            #*************************************************************************************************************
            # Construction des onglets de la fenetre principale
            self.FrameOption( notebook )
            if( self.boxInit != 0 ):
                self.FrameGPSQuickFix( notebook )
                self.FrameBackupRestore( notebook )
                self.FramePoi( notebook )
                self.FramePersonalize( notebook )
            self.FrameAbout( notebook )
            self.FrameQuit( notebook )
            #*************************************************************************************************************
            # Onglet que nous verrons à l'ouverture
            notebook.set_current_page( self.boxInit )
            # Affichage de l'ensemble
            self.window.show_all()

        # Lancement des actions

        # Si l'option a ete fournie, lancement de la sauvegarde de la configuration
        if( self.doSave ):
            self.PutConfig()

        # Si l'option a ete fournie, lancement du GpsFix
        if( self.doGpsFix ):
            self.Debug( 1, "Starting GPSQuickFix" )
            self.GpsQuickFix( None )

        # Si l'option a ete fournie, lancement du Backup
        if( self.doBackup ):
            self.Debug( 1, "Starting Backup" )
            self.BackupRestoreGPS( None, "backup" )

        # Si l'option a ete fournie, lancement de la restauration
        if( self.doRestore ):
            self.Debug( 1, "Starting Restore" )

        # Si on est en mode script, fermeture de l'application
        if( self.noGui == True ):
            self.Delete( None )
            return None

        if( self.gpsStatus != "connected" ):
            self.Popup( _( "Connect your device and reload " ) + App )
            #self.Delete( None )
            #return None

        return None


#----------------------------------------------- DEFINITION DES FONCTIONS GLOBALES -------------------------------------------
def main():
    gtk.main()
    return 0

#----------------------------------------------- LAUNCHING APPLICATION --------------------------------------------------
if __name__ == "__main__":
    NotebookTomtom()
    main()
