#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>


int main(int argc, char *argv[]) {
    setuid(0);
    system("cp -f ~/.ssh/known_hosts /root/.ssh/known_hosts");
    return 0;
}
