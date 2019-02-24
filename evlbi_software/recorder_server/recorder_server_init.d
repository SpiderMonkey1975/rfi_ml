#!/bin/sh
SERVER_BIN=/home/vlbi/bin/recorder_server_threads
DEFAULT_USER=vlbi
CONFIG_FILE=/home/vlbi/recorder/recorder_disks.conf
if [ ! -x ${SERVER_BIN} ]
then
  exit
fi

if [ ! -f ${CONFIG_FILE} ]
then
  exit
fi

: ${username=`whoami`}
[ "$username" == "$DEFAULT_USER" ] && USER_RUN=
[ "$username" != "$DEFAULT_USER" ] && USER_RUN="--chuid $DEFAULT_USER"

case "${1}" in
("start")
    echo -n "Starting eVLBI recorder server: "
    /sbin/start-stop-daemon --start --quiet --background \
            --exec "${SERVER_BIN}" $USER_RUN
    case $? in
    (0)
        echo "recorder_server."
        exit 0
        ;;
    (1)
        echo "recorder_server (already running)."
        exit 0
        ;;
    (*)
        echo "(failed)."
        exit 1
        ;;
    esac
    ;;
("stop")
    echo -n "Stopping eVLBI recorder server: "
    /sbin/start-stop-daemon --stop --retry=1 --quiet --oknodo --signal INT --exec "${SERVER_BIN}"
    echo "recorder_server."
    exit 0
    ;;
("restart" | "force-reload")
    "${0}" stop
    "${0}" start
    ;;
(*)
    echo "Usage: /etc/init.d/recorder_server {start|stop|restart|force-reload}" >&2
    exit 3
    ;;
esac
