/*

  Andy Wang

  A front end driver for libretro

  Program Outline TODO:

    The server sends a byte as a "prompt" to say it's ready; let's say it sends 0.
    The client sends a message like this:
    Command ID, ...
    Where the ... depends on the command.
    Commands can be:
    a. Step the emulator, collecting these informations, expecting this many players and this many inputs, and here are the inputs; (number of bytes per player input will be different for different consoles)
    b. Save a state
    c. Load a state, here it is

  TODO:
    Make scanRoms() and scanCores() flexible

  Python extracting information.

  Impose a grid over the screen the of the game

  Knowing what parts of the screen is scrolling and what sprites are moving

*/

//Native headers used
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <dirent.h>
#include <string.h>
#include <sys/stat.h>
#include <dlfcn.h> //

#include "libretro.h"

/*
Libretro API struct

See libretro.h for more information on what the functions do
*/
static struct {

  void *pointer; //pointer to the API

  void (*retro_init)(void);

  void (*retro_api_version)(void);

  void (*retro_get_system_info)(struct retro_system_info *info);

  void (*retro_unload_game)(void);

  void (*retro_load_game)(const struct retro_game_info *game);

  void (*retro_run)(void);

  void (*retro_reset)(void);

  void (*retro_deinit)(void);

	bool ready; //is the API ready to go

} api;

/*
Dynamically read
*/
#define link(V, S) do {\
	if (!((*(void**)&V) = dlsym(api.pointer, #S))) \
	   printf("API function failedddd '" #S "'': %s", dlerror()); \
	} while (0)
#define retro_link(S) link(api.S, S)

//Arrays to hold a list of stuff in a directory
char* roms[100];
char* cores[10];

//File pointer array
FILE *romFile[100];
FILE *coreFile[100];

/*
scanRoms()
Looks in ROMS directory and returns the files in it. (If any)
*/
void scanRoms(){

    //
    DIR *currDir;
    struct dirent *dir;
    struct stat statbuf;

    currDir = opendir("./ROMS");

    //
    int count = 0;

    if (currDir){

      while ((dir = readdir(currDir)) != NULL) {

        //lstat() gets a link to the file
        lstat(dir->d_name,&statbuf);

        //If the files are any of these
        if(strcmp(".",dir->d_name) == 0 || strcmp("..",dir->d_name) == 0 || strcmp(".DS_Store",dir->d_name) == 0){
               //Nothing to print here, move onto next interation without finishing below
               continue;
         }

         //Add the file to array
         roms[count] = dir->d_name;

         //Print name
         printf("[%d] %s \n", count, dir->d_name);

         //
         count++;

      }

      closedir(currDir);
    }

}

/*
scanCores()

Returns list of cores in a folder

sidenote: connect the two functions
*/

void scanCores(){

    DIR *currDir;
    struct dirent *dir;
    struct stat statbuf;

    currDir = opendir("./cores");

    //
    int count = 0;

    if (currDir){

      while ((dir = readdir(currDir)) != NULL) {

        //lstat() gets a link to the file
        lstat(dir->d_name,&statbuf);

        //If the files are any of these
        if(strcmp(".",dir->d_name) == 0 || strcmp("..",dir->d_name) == 0 || strcmp(".DS_Store",dir->d_name) == 0){
               //Nothing to print here, move onto next interation without finishing below
               continue;
         }

         //Add the file to array
         cores[count] = dir->d_name;

         //Print name
         printf("[%d] %s \n", count, dir->d_name);

         count++;

      }

      closedir(currDir);
    }

}

/*

*/
static void loadGame(const char *rom) {

}

/*

*/
static bool core_environment(unsigned cmd, void *data) {

	return true;

}


/*

*/
static void loadCore(const char *sofile) {

	void (*set_environment)(retro_environment_t) = NULL;

	memset(&api, 0, sizeof(api));

	api.pointer = dlopen(sofile, RTLD_LAZY);

	if (!api.pointer){
		//printf("Failed to load core: %s", dlerror());
    printf("Failed to initialize libretro\n");

	  dlerror();
  }

  //Access the required API function from the library
  retro_link(retro_api_version);
	retro_link(retro_init);
	retro_link(retro_get_system_info);
	retro_link(retro_reset);
	retro_link(retro_load_game);
	retro_link(retro_unload_game);
	retro_link(retro_run);
	retro_link(retro_deinit);


	set_environment(core_environment);

  //Libretro library initialize
  api.retro_init();

  //Core is ready
	api.ready = true;

	printf("Core loaded");

}


/*

main()

format for running the program from command line:

    "main ROMname coreName"

Argc stores number of command-line arguments, with name of program counting as one

Argv stores name of program at argv[0], and then proceeding indices are arguments

*/
int main(int argc, char* argv[]){

  char num[10];

  printf("\nWelcome to desAI.\n\n");

  printf("Now scanning the ROMS folder for possible games to launch.\n\n");

  scanRoms(); //

  printf("\nPlease input the number correlated to your desired target ROM.\n\n");

  //supports up to 100... if the ROM library is huge
  fgets(num, 3, stdin);

  printf("You selected %s\n\n", roms[atoi(num)]);

  scanCores(); //

  printf("Now select your core.\n\n");

  //supports up to 100... if the ROM library is huge
  fgets(num, 3, stdin);

  printf("You selected %s\n\n", cores[atoi(num)]);

  printf("Initializing... \n\n");

  //PASS IN the dylib file
  loadCore();// cores[atoi(num)] );

  printf("Ready!\n\n");

	loadGame( roms[atoi(num)] );


}
