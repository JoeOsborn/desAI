/*

  Andy Wang

  An adapter (front end) for libretro

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
#include "gl.h"
//#include "jpg.h"

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

  void (*retro_get_system_av_info)(struct retro_system_av_info *info);

  void (*retro_unload_game)(void);

  bool (*retro_load_game)(const struct retro_game_info *game);

  void (*retro_run)(void);

  void (*retro_reset)(void);

  void (*retro_deinit)(void);

	bool ready; //is the API ready to go

} api;

//OpenGL API Function links
static struct{

  //unsigned int GLenum;

  //
  void (*glBindTexture) (GLenum target, GLuint texture);

  //
  void (*glReadPixels)(GLint x, GLint y, GLsizei width, GLsizei height, GLenum format, GLenum type, GLvoid *pixels);

} glFuncs;

//void retro_camera_frame_raw(*retro_camera_frame_raw_framebuffer_t);

//retroarch camera frame buffer callback

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
bool core_environment(unsigned command, void *data) {

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
void inputPoll(){

  //Send inputs?

}

/*
inputState()

MATCH THIS :

  typedef int16_t (RETRO_CALLCONV *retro_input_state_t)(unsigned port, unsigned device,
        unsigned index, unsigned id);

*/
int16_t inputState(unsigned port, unsigned device, unsigned index, unsigned id){
  return 1;
}

/*
refreshVid()

MATCHES :
  typedef void (RETRO_CALLCONV *retro_video_refresh_t)(const void *data, unsigned width,
        unsigned height, size_t pitch);

"Pixel format is 15-bit 0RGB1555 native endian"

The number of bytes between the beginning of a scanline and beginning of the next scanline is 512.

*/
void refreshVid(const void *data, unsigned width, unsigned height, size_t pitch){


  //printf("%zu\n", pitch);

  //printf("%d\n", width); 256

  //printf("%d\n", height); 240


   //glFuncs.glBindTexture(0x0DE1, glVars.texture);
   //glFuncs.glBindTexture(GL_TEXTURE_2D, g_video.tex_id);

   //stuff happens
   if(data){

      //FILE* frame = fopen("./images/01.jpg", "wb");

      FILE* dump = fopen("./text/dump.txt", "wb");

      fprintf(dump, "%s\n", data);

      printf("data found\n");

      //GLubyte *data = malloc(3*width*height);

      //pitch = malloc(3*width*height);

      //printf("%p\n",(void*)&data);

      uint16_t *shorts = (uint16_t *)data;

      fprintf(dump, "%hu\n", *shorts);

      printf("------\n");

      for(int i = 0; i < width*height; i+=1) {

        //printf("%hu", shorts);


        uint16_t pixel = shorts[i];
        uint8_t red = 8*(pixel & (0b11111 << 10)) >> 10;
        uint8_t green = 8*(pixel & (0b11111 << 5)) >> 5;
        uint8_t blue = 8*(pixel & (0b11111));

        //red, green, blue are between 0 and 2^6; scale them up to 0..2^8

        printf("%hhu ",red);
        printf("%hhu ",green);
        printf("%hhu    ",blue);

        //fill up another buffer with rgb data to use in opencv to dump

        if (i%width==0){
            printf("\n" );
        }


      }


      //glFuncs.glReadPixels(0, 0, width, height, 0x1907 , 0x1401, data);
      //glFuncs.glReadPixels(0, 0, width, height, GL_RGB , GL_UNSIGNED_BYTE, data);

   }

}



/*
audioSample()

MATCH:
  typedef void (RETRO_CALLCONV *retro_audio_sample_t)(int16_t left, int16_t right);
*/
void audioSample(int16_t left, int16_t right){
  //audio happens

}

/*
audioBatch()

MATCH:
  typedef size_t (RETRO_CALLCONV *retro_audio_sample_batch_t)(const int16_t *data,
        size_t frames);
*/
size_t audioBatch(const int16_t *data, size_t frames){
  //nice
  return frames;
}

/*
loadCore()

Handles the necessary linking and callback

print fuctions were for finding out when segmentation fault occurred.

*/
void loadCore(const char *sofile) {

 /*

 Have to link these, otherwise segmentation fault 11 during retro_run

 RETRO_API void retro_set_environment(retro_environment_t);
 RETRO_API void retro_set_video_refresh(retro_video_refresh_t);
 RETRO_API void retro_set_audio_sample(retro_audio_sample_t);
 RETRO_API void retro_set_audio_sample_batch(retro_audio_sample_batch_t);
 RETRO_API void retro_set_input_poll(retro_input_poll_t);
 RETRO_API void retro_set_input_state(retro_input_state_t);

 */

 //Get things nice and ready
 void (*retro_env)(retro_environment_t) = NULL;

 //Input pair - poll and state
 void (*retro_input)(retro_input_poll_t) = NULL;
 void (*retro_inState)(retro_input_state_t) = NULL;

 //Audio pair
 void (*retro_audio)(retro_audio_sample_t) = NULL;
 void (*retro_audio_batch)(retro_audio_sample_batch_t) = NULL;

 //Visual
 void (*retro_video)(retro_video_refresh_t) = NULL;
 //void (*retro_frame)(retro_camera_frame_raw_framebuffer_t) = NULL;

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

  //yeh
  retro_link(retro_init);

  retro_link(retro_run);

  retro_link(retro_deinit);

  retro_link(retro_load_game);

  retro_link(retro_get_system_info);

  retro_link(retro_get_system_av_info);

  //links: RETRO_API void retro_set_environment(retro_environment_t);
  link(retro_env, retro_set_environment);

  //links: RETRO_API void retro_set_input_poll(retro_input_poll_t);
  link(retro_input, retro_set_input_poll);

  //links: RETRO_API void retro_set_input_state(retro_input_state_t);
  link(retro_inState, retro_set_input_state);

  //links: RETRO_API void retro_set_audio_sample(retro_audio_sample_t);
  link(retro_audio, retro_set_audio_sample);

  //links: RETRO_API void retro_set_audio_sample_batch(retro_audio_sample_batch_t);
  link(retro_audio_batch, retro_set_audio_sample_batch);

  //links: RETRO_API void retro_set_video_refresh(retro_video_refresh_t);
  link(retro_video, retro_set_video_refresh);

  //links:typedef void (RETRO_CALLCONV *retro_camera_frame_raw_framebuffer_t)(const uint32_t *buffer, unsigned width, unsigned height, size_t pitch);
  //link(retro_frame, retro_camera_frame_raw);

  /*
    Link the callbacks to functions existing in the main.c implementation
  */
	retro_env(core_environment);

  retro_input(inputPoll);

  retro_inState(inputState);

  retro_audio(audioSample);

  retro_audio_batch(audioBatch);

  retro_video(refreshVid);

  //retro_frame(frameBuffer);

  //Libretro library initialize
  api.retro_init();

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

  struct retro_system_av_info avinfo = {0};
  struct retro_system_info sys = {0};

  //Declaring the parameter the Libretro API wants
  struct retro_game_info gameInfo = { rom, 0 };

  //Read a non-text file, that is our ROM
  FILE *game = fopen(rom, "rb");

  //No ROM
  if (!game){
    printf("Mission failed, we'll get em next time. \n\n");
  }
  else{
    printf("Are we rushin in, or are we going in sneaky beaky like? (Game file found) \n\n");

    fseek(game, 0, SEEK_END);

    gameInfo.size = ftell(game);

    rewind(game);

    api.retro_get_system_info(&sys);

    gameInfo.data = malloc(gameInfo.size);

    fread((void*)gameInfo.data, gameInfo.size, 1, game);

    if ( !api.retro_load_game(&gameInfo)){
        printf("dead on loading");
    }

    api.retro_get_system_av_info(&avinfo);

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

  int count = 0;
  int frames = 2000;

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

  loadCore("./cores/bnes-libretro/bnes_libretro.dylib");
  //loadCore( cores[atoi(num)] );

  printf("Ready!\n\n");

	//loadGame( roms[atoi(num)] );
  loadGame("./ROMS/Super Mario Bros.nes"); //hard coding master

  //runs super mario for one frame
  while (count < frames){
    api.retro_run();
    count++;
  }

  api.retro_deinit();

  return 0;

}
