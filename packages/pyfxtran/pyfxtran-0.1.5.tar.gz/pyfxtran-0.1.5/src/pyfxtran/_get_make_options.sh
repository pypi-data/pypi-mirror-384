#This script aims at providing make options to build fxtran

ldd_version=$(ldd --version 2>&1)
if echo $ldd_version | grep -i 'GLIBC' 2>&1 > /dev/null; then
  # New GLIBC
  echo -n "STATIC=1"
elif echo $ldd_version | grep -i 'GNU' 2>&1 > /dev/null; then
  # Old GLIBC
  echo -n "STATIC=1"
else
  # At least musl systems
  echo -n "STATIC=1 NO_OBSTACK=1 LDFLAGS=-lintl"
fi
