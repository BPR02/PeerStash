/* 
Peerstash
Copyright (C) 2026 BPR02

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

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
        fprintf(stderr, "Usage: /srv/peerstash/scripts/create_task TASK_NAME SCHEDULE PRUNE_SCHEDULE\n");
        return 1;
    }
    return 0;
}
