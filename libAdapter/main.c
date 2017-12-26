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

#include "bmpfile.h"
#include "libretro.h"

//Arrays to hold a list of stuff in a directory
char* roms[100];
char* cores[10];

//Each index corresponds to a button
uint16_t controls[16];

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

  void (*retro_set_controller_port_device)(unsigned port, unsigned device);

	bool ready; //is the API ready to go

} api;



//int toggle = 0;

/*
Dynamically read
*/
#define link(V, S) do {\
	if (!((*(void**)&V) = dlsym(api.pointer, #S))) \
	   printf("API function failedddd '" #S "'': %s", dlerror()); \
	} while (0)
#define retro_link(S) link(api.S, S)


/*
core_environment()

The section of the adapter to make environment callbacks

See around line 450 of the libretro.h file

*/
bool core_environment(unsigned command, void *data) {

  switch(command){

    //set the input num_descriptors
    case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:
      return 1;

  }

	return true;

}

/*
inputPoll()
*/
void inputPoll(){
}

/*
inputState()

MATCH THIS :

  typedef int16_t (RETRO_CALLCONV *retro_input_state_t)(unsigned port, unsigned device,
        unsigned index, unsigned id);


    #define RETRO_DEVICE_ID_JOYPAD_B        0
    #define RETRO_DEVICE_ID_JOYPAD_Y        1
    #define RETRO_DEVICE_ID_JOYPAD_SELECT   2
    #define RETRO_DEVICE_ID_JOYPAD_START    3
    #define RETRO_DEVICE_ID_JOYPAD_UP       4
    #define RETRO_DEVICE_ID_JOYPAD_DOWN     5
    #define RETRO_DEVICE_ID_JOYPAD_LEFT     6
    #define RETRO_DEVICE_ID_JOYPAD_RIGHT    7
    #define RETRO_DEVICE_ID_JOYPAD_A        8
    #define RETRO_DEVICE_ID_JOYPAD_X        9
    #define RETRO_DEVICE_ID_JOYPAD_L       10
    #define RETRO_DEVICE_ID_JOYPAD_R       11
    #define RETRO_DEVICE_ID_JOYPAD_L2      12
    #define RETRO_DEVICE_ID_JOYPAD_R2      13
    #define RETRO_DEVICE_ID_JOYPAD_L3      14
    #define RETRO_DEVICE_ID_JOYPAD_R3      15

*/
int16_t inputState(unsigned port, unsigned device, unsigned index, unsigned id){

  int randIn = rand()%8;

  printf("%d\n", randIn);

  if(id == randIn) {
    return 1;
  }


  return 0;

  //array of ints/bools take input specs from controller
  //loop
  //c++ pipe example and iostream
}

/*
refreshVid()

MATCHES :
  typedef void (RETRO_CALLCONV *retro_video_refresh_t)(const void *data, unsigned width,
        unsigned height, size_t pitch);

"Pixel format is 15-bit 0RGB1555 native endian"

The number of bytes between the beginning of a scanline and beginning of the next scanline is 512.

*/
int filecount = 0;

void refreshVid(const void *data, unsigned width, unsigned height, size_t pitch){

  //printf("Width: %d", width);//256
  //printf("Height: %d", height);//240

  char name[100];

   //stuff happens
   if(data){

      printf("data found\n");

      //printf("%p\n",(void*)&data);

      uint16_t *shorts = (uint16_t *)data;

      printf("------\n");

      //see bmpfile.h
      bmpfile_t *myBmp;

      if ((myBmp = bmp_create((width), (height), 8) ) == NULL){

        printf("Sharks byte and they hurt. \n" );

        exit(0);

      }

      int j, i;

      //for (int i=0; i<width*height; i++){

      for (int i=0; i < width; i++){


        for (int j=0; j<height; j++){

          uint16_t pixel = shorts[i+j*width];

          //printf("pixel  %d", pixel);

          /*red, green, blue are between 0 and 2^6; scale them up to 0..2^8

          - n bits yield 2^n patterns
          - 0b just denotes the numbers on the right of it is a binary literal, or base two number
          - remember an n bit is for teh alpha but we are only currently looking at RGB
                                            111110000000000
          1) 11111 is shifted left by 10 == 111110000000000 or 31744 (decimal)
          2) pixel value (1585560) or (110000011000110011000 in binary) AND  31744 occurs == 12288 (decimal)
          3) multiply 12288 (11000000000000 in binary) by 8 (1000) == 98304
          4) bitwise shift right by 10 == 96


          so to shift to 2^8 that's like two more bits needed for shifts

          */

          //120 120 120
          uint16_t red = 8*(pixel & (0b11111 << 10)) >> 10;
          uint16_t green = 8*(pixel & (0b11111 << 5)) >> 5;
          uint16_t blue = 8*(pixel & (0b11111));

          //61 red 61 green 111 blue
          //uint16_t red = 2*(pixel & (0b11111111 << 7)) >> 7;
          //uint16_t green = 2*(pixel & (0b1111111 << 3)) >> 3;
          //uint16_t blue = (pixel & (0b1111111));

          //printf("%hu red ", red);
          //printf("%hu green ", green);
          //printf("%hu blue ", blue);

          if (j%width==0){

              //printf("\n\n" );

          }


          //printf("x: %d , y: %d", i,j);

          /*
            Define the rgba

            Set the pixels structure where :

            typedef struct {
              uint8_t blue;
              uint8_t green;
              uint8_t red;
              uint8_t alpha;
            } rgb_pixel_t;
          */

          rgb_pixel_t currPixel = {(uint8_t)blue, (uint8_t)green, (uint8_t)red, (uint8_t)0};

          //Set the pixel : bool bmp_set_pixel(bmpfile_t *bmp, uint32_t x, uint32_t y, rgb_pixel_t pixel);
          bmp_set_pixel(myBmp, (uint32_t)(i), (uint32_t)(j), currPixel);

        }

      }

      //snprintf();

      //Save the bmp file
      if (filecount%2==0){
        sprintf(name, "%s%d%s", "./images/", filecount, ".bmp");
        bmp_save(myBmp, name);
        bmp_destroy(myBmp);
      }

      filecount++;

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

  retro_link(retro_set_controller_port_device);

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
  int frames = 300;

  char num[10];

  //printf("\nWelcome to desAI.\n\n");

  //printf("Now scanning the ROMS folder for possible games to launch.\n\n");

  //scanRoms(); //

  //printf("\nPlease input the number correlated to your desired target ROM.\n\n");

  //supports up to 100... if the ROM library is huge
  //fgets(num, 3, stdin);

//  printf("\nYou selected %s\n\n", roms[atoi(num)]);

//  scanCores(); //

//  printf("Now select your core.\n\n");

  //supports up to 100... if the ROM library is huge
//  fgets(num, 3, stdin);

//  printf("You selected %s\n\n", cores[atoi(num)]);

//  printf("Initializing... \n\n");

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

    for (int i=0; i<16; i++){
      controls[i] = (rand() % 1);
    }

    count++;


  }

  //api.retro_deinit();

  return 0;

}

/*
scanCores()

Returns list of cores in a folder

sidenote: connect the two functions


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
*/

/*
scanRoms()
Looks in ROMS directory and returns the files in it. (If any)

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
*/
