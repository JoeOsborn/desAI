CXX=clang++
CXXFLAGS=-I. -std=c++11 -g -fsanitize=address -fsanitize=undefined -mmacosx-version-min=10.12
DEPS = libretro.h 
OBJ = main.o

%.o: %.cpp $(DEPS)
	$(CXX) -c -o $@ $< $(CXXFLAGS)

driver: $(OBJ)
	$(CXX) -o $@ $^ $(CXXFLAGS)

.PHONY: clean

clean:
	rm -f *.o driver 
