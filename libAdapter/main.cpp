/*

  Andy Wang, Joseph Osborn

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

#include <cstdio>
#include <iostream>
#include <sstream>
#include <tuple>

#ifdef _WIN32
# include <io.h>
# include <fcntl.h>
# define SET_BINARY_MODE(handle) setmode(handle, O_BINARY)
#else
# define SET_BINARY_MODE(handle) ((void)0)
#endif

//Native headers used
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <dirent.h>
#include <string.h>
#include <sys/stat.h>
#include <dlfcn.h>
#include <assert.h>

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

  void (*retro_get_system_av_info)(struct retro_system_av_info *info);

  size_t (*retro_serialize_size)(void);

  bool (*retro_serialize)(void*, size_t);

  bool (*retro_unserialize)(const void*,size_t);

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
#define link(V, S) do {                                                 \
    if (!((*(void**)&V) = dlsym(api.pointer, #S)))                      \
      std::cerr << ("API function failedddd '" #S "'': %s", dlerror()); \
  } while (0)
#define retro_link(S) link(api.S, S)

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
//Each index corresponds to a button
uint16_t controls[2][16];
int16_t inputState(unsigned port, unsigned device, unsigned index, unsigned id){
  assert(port < 2);
  assert(index == 0);
  assert(device == 1);
  return controls[port][id];
}

/*
  refreshVid()

  MATCHES :
  typedef void (RETRO_CALLCONV *retro_video_refresh_t)(const void *data, unsigned width,
  unsigned height, size_t pitch);

  "Pixel format is 15-bit 0RGB1555 native endian"

  The number of bytes between the beginning of a scanline and beginning of the next scanline is 512.

*/

//TODO: generalize, use retro_game_geometry
uint16_t fbWidth = 256;
uint16_t fbHeight = 240;
uint8_t fbDepth = 3;
uint32_t fb[240*256];

void refreshVid(const void *data, unsigned width, unsigned height, size_t pitch){
  assert(fbWidth == width);
  assert(fbHeight == height);

  //stuff happens
  if(data){
    // TODO: handle different pitch
    uint16_t *shorts = (uint16_t *)data;
    for (uint16_t j=0; j < height; j++){
      for (uint16_t i=0; i < width; i++){
        uint16_t pixel = shorts[i+j*width];
        /*red, green, blue are between 0 and 2^6; scale them up to 0..2^8

          - n bits yield 2^n patterns
          - 0b just denotes the numbers on the right of it is a binary literal, or base two number
          - remember an n bit is for the alpha but we are only currently looking at RGB
          111110000000000
          1) 11111 is shifted left by 10 == 111110000000000 or 31744 (decimal)
          2) pixel value (1585560) or (110000011000110011000 in binary) AND  31744 occurs == 12288 (decimal)
          3) multiply 12288 (11000000000000 in binary) by 8 (1000) == 98304
          4) bitwise shift right by 10 == 96

          so to shift to 2^8 that's like two more bits needed for shifts
        */

        //120 120 120
        uint8_t red = 8*(pixel & (0b11111 << 10)) >> 10;
        uint8_t green = 8*(pixel & (0b11111 << 5)) >> 5;
        uint8_t blue = 8*(pixel & (0b11111));
        fb[i+j*width] = (uint32_t)(0xFF << 24 | red << 16 | green << 8 | blue);
      }
    }
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

bool core_environment(unsigned command, void *data) {
  std::cerr<<"ENV "<<command<<"\n";
	return true;
}


/*
  loadCore()

  Handles the necessary linking and callback

  print fuctions were for finding out when segmentation fault occurred.

*/
bool loadCore(const char *sofile) {

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

  memset(&api, 0, sizeof(api));

  //resolve symbols lazily
  api.pointer = dlopen(sofile, RTLD_LAZY);

  if (!api.pointer){
    std::cerr << ("Failed to initialize libretro\n");

    dlerror();
    return false;
  }

  //yeh
  retro_link(retro_init);

  retro_link(retro_run);

  retro_link(retro_deinit);

  retro_link(retro_load_game);

  retro_link(retro_serialize_size);

  retro_link(retro_serialize);

  retro_link(retro_unserialize);

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

  return true;
}


/*
  loadGame()

  Loads the game

  Define a struct for :

  RETRO_API bool retro_load_game(const struct retro_game_info *game);

*/
bool loadGame(const char *rom) {

  struct retro_system_av_info avinfo={0};
  struct retro_system_info sys={0};

  //Declaring the parameter the Libretro API wants
  struct retro_game_info gameInfo = { rom, 0, 0, 0 };
  //  rom = realpath(rom, NULL);
  //Read a non-text file, that is our ROM
  FILE *game = fopen(rom, "rb");

  //No ROM
  if (!game){
    return false;
  }

  fseek(game, 0, SEEK_END);
  gameInfo.size = ftell(game);

  rewind(game);

  api.retro_get_system_info(&sys);

  gameInfo.data = malloc(gameInfo.size);

  fread((void*)gameInfo.data, gameInfo.size, 1, game);

  if ( !api.retro_load_game(&gameInfo)){
    return false;
  }

  api.retro_get_system_av_info(&avinfo);

  return true;

}

uint32_t save_size = 0;
uint8_t *saveBuffer = NULL;

void DoSaveState() {
  if(!saveBuffer || save_size != api.retro_serialize_size()) {
    save_size = api.retro_serialize_size();
    assert(save_size);
    saveBuffer = (uint8_t*)calloc(save_size, sizeof(uint8_t));
    assert(saveBuffer);
  }
  api.retro_serialize(saveBuffer, save_size);
}

void DoLoadState() {
  assert(saveBuffer);
  assert(save_size == api.retro_serialize_size());
  api.retro_unserialize(saveBuffer, save_size);
}

void RunOneFrame(uint16_t p1, uint16_t p2) {
  uint16_t players[] = {p1,p2};
  for(uint8_t player = 0; player < 2; player++) {
    for(uint8_t idx = 0; idx < 16; idx++) {
      controls[player][idx] = players[player] & (1 << idx);
    }
  }
  api.retro_run();
}

enum InfoMask {
               None=0,
               FB=1<<0,
               Audio=1<<1
};

enum CtrlCommand {
                  Step=0, //Infos NumPlayers NumMovesMSB NumMovesLSB
                  // -> steps emu. One FB, AudioBuffers per move if infos are set
                  GetState=1, // -> state length, state
                  LoadState=2 //LoadState, infos, statelen, statebuf
                  // -> loads state; if infos & FB, sends framebuffer, if infos & Audio, sends audio samples
};

template<typename T> void write_seq(std::ostream &strm, const T* data, size_t count) {
  strm.write((const char *)(data), sizeof(T)*count);
}

template<typename T> void write_obj(std::ostream &strm, T thing) {
  strm.write((const char *)(&thing), sizeof(T));
}

void SendFramebuffer(std::ostream &stream) {
  stream.write((const char *)fb, sizeof(uint32_t)*fbWidth*fbHeight);
  //TODO: check stream error flags??
}

void SendReady(std::ostream &str) {
  write_obj(str, (uint8_t)0);
  str.flush();
}

int main(int argc, char**argv) {
  //std::setvbuf(stdout,NULL,_IONBF,1024*1024*8);
  SET_BINARY_MODE(stdin);
  SET_BINARY_MODE(stdout);
  auto instr = stdin;
  std::ostream& outstr = std::cout;

  std::cerr << ("Ready!\n\n");

  if(argc < 3) {
    std::cerr << "Not enough arguments, please include a core and a ROM file path!\n";
    abort();
  }
  std::cerr<<"Load core\n";
  if(!loadCore(argv[1])) {
    std::cerr << "Couldn't start up core " << std::string(argv[1]) << "\n";
    abort();
  }
  std::cerr<<"Load game\n";
  if(!loadGame(argv[2])) {
    std::cerr << std::string(argv[2])+" ROM not opened!\n";
    abort();
  }

  std::cerr<<"Good to go\n";

  //TODO: test everything from python!

  uint8_t cmd_buf[1024*1024];
  while(1) {
    std::cerr << "Send ready\n";
    SendReady(outstr);
    size_t read = std::fread(cmd_buf, sizeof(uint8_t), 1, instr);
    if(read == 0) { break; }
    size_t stateLen;
    InfoMask infos=None;
    uint16_t numMoves=0;
    uint8_t numMovesLSB=0, numMovesMSB=0, bytesPerPlayer=0, numPlayers=0;
    CtrlCommand cmd = (CtrlCommand)cmd_buf[0];
    switch(cmd) {
    case Step:
      std::cerr << "start send\n";
      //get the next parts of the command:
      read = std::fread(cmd_buf, sizeof(uint8_t), 5, instr);
      if(read != 5) {
        std::cerr << "Wrong number of bytes in Step command!\n";
        abort();
      }
      infos = (InfoMask)cmd_buf[0];
      // TODO: generalize past these limits using retro input descriptors
      numPlayers = cmd_buf[1];
      if(numPlayers > 4) {
        std::cerr << "NES is only up to four players!\n";
        abort();
      }
      bytesPerPlayer = 2;
      numMovesLSB = cmd_buf[3];
      numMovesMSB = cmd_buf[4];
      numMoves = ((uint16_t)numMovesMSB << 8) | (uint16_t)numMovesLSB;
      if(numMoves == 0) {
        std::cerr << "Got to give at least one move!\n";
        abort();
      }
      if((int32_t)(numMoves*bytesPerPlayer*numPlayers) > 65536) {
        std::cerr << "Too many moves, sorry!\n";
      }
      //We have to read everything off the pipe before we can start sending our stuff.
      read = std::fread(cmd_buf, bytesPerPlayer, numMoves*numPlayers, instr);
      if(read != numPlayers*numMoves) {
        std::cerr << "Ran out of bytes too early!\n";
        abort();
      }
      for(int i = 0; i < numMoves*numPlayers; i+=numPlayers*bytesPerPlayer) {
        // TODO: generalize beyond two bytes per move
        uint16_t p1Move = cmd_buf[i] << 8 | cmd_buf[i+1];
        uint16_t p2Move = numPlayers == 2 ? (cmd_buf[i+2] << 8 | cmd_buf[i+3]) : 0;
        RunOneFrame(p1Move, p2Move);
        //once per frame
        if(infos & FB) {
          SendFramebuffer(outstr);
        }
        if(infos & Audio) {
          //SendAudioBuffer(outstr);
        }
        //Flush after each step so the other side can read
        outstr.flush();
        std::cerr.flush();
      }
      break;
    case GetState:
      //GetState
      DoSaveState();
      //write that to stdout (native order)
      write_obj(outstr, (uint32_t) save_size);
      // The one legit use we have for <<
      write_seq<uint8_t>(outstr, saveBuffer, save_size);
      break;
    case LoadState:
      //LoadState, infos, statelen, statebuf
      read = std::fread(cmd_buf, sizeof(uint8_t), 1, instr);
      if(read != 1) {
        std::cerr << "Couldn't read enough bytes in loadstate metadata A\n";
        abort();
      }
      infos = (InfoMask)cmd_buf[0];
      // native order
      read = std::fread(cmd_buf, sizeof(uint32_t), 1, instr);
      if(read != sizeof(uint32_t)) {
        std::cerr << "Couldn't read enough bytes in loadstate metadata B\n";
        abort();
      }
      stateLen = *((uint32_t*)(cmd_buf));
      assert(stateLen == save_size);
      read = std::fread(saveBuffer, sizeof(uint8_t), stateLen, instr);
      if(read != stateLen) {
        std::cerr << "Couldn't read enough bytes in loadstate payload\n";
        abort();
      }
      if(infos & FB) {
        SendFramebuffer(outstr);
      }
      if(infos & Audio) {
        //SendAudiobuffer(outstr);
      }
      break;
    default:
      break;
    }
  }
  return 0;
}
