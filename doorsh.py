#!/usr/bin/env python

import cmd
import sys

import doorctl

class DoorShell(cmd.Cmd):
    prompt = 'doorbot> '

    def get_args(self, line):
        return [ x for x in line.split(' ') if x != '' ]

    def __init__(self):
        cmd.Cmd.__init__(self)

    def do_list(self, line):
        """list"""
        doorctl.list_users()

    def do_enable(self, line):
        """enable <fobid>"""
        for rfid in self.get_args(line):
            doorctl.enable(rfid)

    def do_disable(self, line):
        """disable <fobid>"""
        for rfid in self.get_args(line):
            doorctl.disable(rfid)

    def do_delete(self, line):
        """delete <fobid>"""
        for rfid in self.get_args(line):
            doorctl.delete(rfid)

    def do_addkey(self, line):
        """addkey [<fobid> <pin>]"""
        args = self.get_args(line)
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

    def do_openmode(self, line):
        """openmode"""
        doorctl.socket_command('openmode')

    def do_authmode(self, line):
        """authmode"""
        doorctl.socket_command('authmode')

    def do_resetpin(self, line):
        """resetpin [<fobid> <pin>]"""
        args = self.get_args(line)
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

    def do_shutdown(self, line):
        """shutdown"""
        doorctl.socket_command('shutdown')

    def do_restart(self, line):
        """restart"""
        doorctl.socket_command('restart')

    def do_quit(self, line):
        """quit"""
        sys.exit(0)

    def do_EOF(self, line):
        """quit"""
        sys.exit(0)

if __name__ == '__main__':
    DoorShell().cmdloop()
