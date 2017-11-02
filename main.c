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

 "Function pointers are useful for passing functions as parameters to other functions.
 ... So basically, it gives C pseudo first-class functionality."

 OOP

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
         printf("[%d] %s \n\n", count, dir->d_name);

         count++;

      }

      closedir(currDir);
    }

}

/*
core_environment()

The section of the adapter to make environment callbacks

See around line 450 of the libretro.h file

*/
static bool core_environment(unsigned command, void *data) {

  switch(command){

    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
    case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:
        *(const char **)data = ".";
        return true;
  }

	return true;

}

/*
inputPoll()
*/
static void inputPoll(){

  //Send inputs?

}

/*
inputState()

MATCH THIS :

typedef int16_t (RETRO_CALLCONV *retro_input_state_t)(unsigned port, unsigned device,
      unsigned index, unsigned id);

*/
static int16_t inputState(unsigned port, unsigned device, unsigned index, unsigned id){
  return 0;
}

/*
loadCore()

Handles the necessary linking and callback

print fuctions were for finding out when segmentation fault occurred.

*/
static void loadCore(const char *sofile) {

 //Get things nice and ready
 void (*set_environment)(retro_environment_t) = NULL;

 //input poll and state are a pair; otherwise seg fault 11
 void (*get_input)(retro_input_poll_t) = NULL;
 void (*get_state)(retro_input_state_t) = NULL;

  //printf("two\n" );

 memset(&api, 0, sizeof(api));

  //printf("thre\n" );

  //resolve symbols lazily
  api.pointer = dlopen(sofile, RTLD_LAZY);

 //printf("four\n" );
	if (!api.pointer){
    printf("Failed to initialize libretro\n");

	  dlerror();
  }

  //
  retro_link(retro_init);

  //links: RETRO_API void retro_set_environment(retro_environment_t);
  link(set_environment, retro_set_environment);

  printf("five\n" );

  //links: RETRO_API void retro_set_input_poll(retro_input_poll_t);
  link(get_input, retro_set_input_poll);

  //links: RETRO_API void retro_set_input_state(retro_input_state_t);
  link(get_state, retro_set_input_state);

  printf("six\n" );

	set_environment(core_environment);

  printf("seven\n" );

  get_input(inputPoll);

  printf("eight \n");

  get_state(inputState);

  printf("nine \n");

  //Libretro library initialize
  api.retro_init();

  printf("ten \n");

  //Core is ready
	api.ready = true;

	printf("Core loaded \n\n");

}

/*
loadGame()

Loads the game

Define a struct for :

  RETRO_API bool retro_load_game(const struct retro_game_info *game);

*/
static void loadGame(const char *rom) {

  //Declaring the parameter the Libretro API wants
  struct retro_game_info gameInfo;

  //Read a non-text file, that is our ROM
  FILE *game = fopen(rom, "rb");

  //No ROM
  if (!game){
    printf("Mission failed, we'll get em next time. \n\n");
  }
  else{
    printf("Are we rushin in, or are we going in sneaky beaky like? (Game file found) \n\n");

    //
    return;

  }

}


/*
main()

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

  printf("\nYou selected %s\n\n", roms[atoi(num)]);

  scanCores(); //

  printf("Now select your core.\n\n");

  //supports up to 100... if the ROM library is huge
  fgets(num, 3, stdin);

  printf("You selected %s\n\n", cores[atoi(num)]);

  printf("Initializing... \n\n");

  //PASS IN the dylib file
  //printf("./cores/%s/libretro/quicknes_libretro.dylib", cores[atoi(num)]);

  loadCore("./cores/quickNES/libretro/quicknes_libretro.dylib");
  //loadCore( cores[atoi(num)] );

  printf("Ready!\n\n");

	//loadGame( roms[atoi(num)] );
  loadGame("./ROMS/Super Mario Bros.nes"); //hard coding master

  /*
  segfault on retro_run... but why?
    probably need to implement the rest of the set functions
  */
  api.retro_run();

}
