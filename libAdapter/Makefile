CPP=clang++
CPPFLAGS=-I. -std=c++11 -g -fsanitize=address -fsanitize=undefined 
DEPS = libretro.h 
OBJ = main.o

%.o: %.cpp $(DEPS)
	$(CPP) -c -o $@ $< $(CPPFLAGS)

driver: $(OBJ)
	$(CPP) -o $@ $^ $(CPPFLAGS)

.PHONY: clean

clean:
	rm -f *.o driver 
