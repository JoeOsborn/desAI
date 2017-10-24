/*

Andy Wang

A command line front-end for libretro developed to study game-design

Program Outline:

  The server sends a byte as a "prompt" to say it's ready; let's say it sends 0.
  The client sends a message like this:
  Command ID, ...
  Where the ... depends on the command.
  Commands can be:
  a. Step the emulator, collecting these informations, expecting this many players and this many inputs, and here are the inputs; (number of bytes per player input will be different for different consoles)
  b. Save a state
  c. Load a state, here it is

Project Dependencies:

  http://glew.sourceforge.net/index.html for cross-platform OpenGL goodness
  http://www.glfw.org/ for UI

  FOR MAC USERS:
    'brew install --build-bottle --static glfw3'

  http://www.portaudio.com for cross-platform audio

FILE type is used in streams and is included in stdio.h

*/

//Native headers used
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <dirent.h>
#include <string.h>
#include <sys/stat.h>

//External header files included - see top comment for info
#include <GL/glew.h>
#include <GLFW/glfw3.h>
#include <portaudio.h>
#include "libretro.h"

//
char* roms[100];
static GLFWwindow* window; //

/*
scanDir()
Looks in a directory and returns the files in it. (If any)
*/
void scanDir(){

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

         count++;

      }

      closedir(currDir);
    }

}

/*
Starts a libretro core to run the ROM
*/
void init(){


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

  scanDir();

  printf("\nPlease input the number correlated to your desired target ROM.\n\n");

  //supports up to 100... if the ROM library is huge
  fgets(num, 3, stdin);

  printf("You selected %s\n\n", roms[atoi(num)]);

  //
  printf("Initializing... \n\n");

  init();

  //
  printf("Ready!\n\n");

/*

  //GLFW Example code below
  if (!glfwInit()){
    return -1;
  }
  */


  /*
  Create a windowed mode window and its OpenGL context
  */
  /*
  window = glfwCreateWindow(640, 480, "Hello World", NULL, NULL);
  if (!window)
  {
      glfwTerminate();
      return -1;
  }
  */

  /* Make the window's context current */
//  glfwMakeContextCurrent(window);

  /* Loop until the user closes the window */

  //while (!glfwWindowShouldClose(window)){
      /* Render here */
    //  glClear(GL_COLOR_BUFFER_BIT);

      /* Swap front and back buffers */
    //  glfwSwapBuffers(window);

      /* Poll for and process events */
    //  glfwPollEvents();
  //}

  //glfwTerminate();

//  return 0;


  //printf("%s\n", roms[0]);

  //return (0);

}
