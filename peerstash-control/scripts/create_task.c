#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>


int main(int argc, char *argv[]) {
    if (argc == 4) {
        setuid(0);
        char command[255];
        sprintf(command, "/srv/peerstash/scripts/create_task.sh %s %s %s", argv[1], argv[2], argv[3]); 
        system(command); 
    }
    else {
        fprintf(2, "Usage: /srv/peerstash/scripts/create_task TASK_NAME SCHEDULE PRUNE_SCHEDULE");
        return 1;
    }
    return 0;
}
