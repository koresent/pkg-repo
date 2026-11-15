#!/bin/sh
export LD_LIBRARY_PATH="/usr/lib/photocraft-companion:/opt/cuda/lib64:${LD_LIBRARY_PATH}"
exec /usr/lib/photocraft-companion/photocraft-companion "$@"
