#!/usr/bin/env python

import cmd
import sys

import doorctl

class DoorShell(cmd.Cmd):
    prompt = 'doorbot> '

    def __init__(self):
        cmd.Cmd.__init__(self)

    def do_list(self, arg):
        """list"""
        doorctl.list_users()

    def do_enable(self, arg):
        """enable <fobid>"""
        for rfid in arg.strip(' ').rstrip(' ').split(' '):
            doorctl.enable(rfid)

    def do_disable(self, arg):
        """disable <fobid>"""
        for rfid in arg.strip(' ').rstrip(' ').split(' '):
            doorctl.disable(rfid)

    def do_delete(self, arg):
        """delete <fobid>"""
        for rfid in arg.strip(' ').rstrip(' ').split(' '):
            doorctl.delete(rfid)

    def do_addkey(self, arg):
        """addkey [<fobid> <pin>]"""
        args = arg.strip(' ').rstrip(' ').split(' ')
        if len(args) == 0:
            doorctl.socket_command('addkey')
        elif len(args) == 2:
            try:
                doorctl.import_user(args[0], '1', args[1], plain=True)
                print "ok"
            except ValueError as e:
                print e
        else:
            print "usage: addkey [<fobid> <pin>]"

    def do_openmode(self, arg):
        """openmode"""
        doorctl.socket_command('openmode')

    def do_authmode(self, arg):
        """authmode"""
        doorctl.socket_command('authmode')

    def do_resetpin(self, arg):
        """resetpin [<fobid> <pin>]"""
        args = arg.strip(' ').rstrip(' ').split(' ')
        if len(args) == 0:
            doorctl.socket_command('resetpin')
        elif len(args) == 2:
            try:
                doorctl.change_pin(args[0], args[1])
                print "ok"
            except ValueError as e:
                print e
        else:
            print "usage: resetpin [<fobid> <pin>]"

    def do_shutdown(self, arg):
        """shutdown"""
        doorctl.socket_command('shutdown')

    def do_restart(self, arg):
        """restart"""
        doorctl.socket_command('restart')

    def do_quit(self, arg):
        """quit"""
        sys.exit(0)

    def do_EOF(self, arg):
        """quit"""
        sys.exit(0)

if __name__ == '__main__':
    DoorShell().cmdloop()
