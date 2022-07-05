#%%
import numpy as np
import pandas as pd
import sys

np.set_printoptions(threshold=sys.maxsize)

def startPoint(x):
    y = np.random.randint(0,x)
    while y%2==0:
        y = np.random.randint(0,x)
    return y

def directionGenerator():
    k=np.arange(1,5,dtype=int)
    np.random.shuffle(k)
    return k

def generateMaze(a,r,c,height,width):
    a=a
    h=height
    w=width
    directions = directionGenerator()
    # k = np.random.randint(1,5,dtype=int)
    for k in directions:
        if k == 1:
            # up
            if r-2 <= 0:
                pass
            else:
                if a[r-2,c] != 0:
                    a[r-2,c] = 0
                    a[r-1,c] = 0
                    generateMaze(a,r-2,c,h,w)
        elif k == 2:
            # down
            if r+2 >= h - 1:
                pass
            else:
                if a[r+2,c] != 0:
                    a[r+2,c] = 0
                    a[r+1,c] = 0
                    generateMaze(a,r+2,c,h,w)
        elif k == 3:        
            # left
            if c-2 <= 0:
                pass
            else:
                if a[r,c-2] != 0:
                    a[r,c-2] = 0
                    a[r,c-1] = 0
                    generateMaze(a,r,c-2,h,w)
        else:               
            # right
            if c+2 >= w-1:
                pass
            else:
                if a[r,c+2] != 0:
                    a[r,c+2] = 0
                    a[r,c+1] = 0
                    generateMaze(a,r,c+2,h,w)

def maze(size):
    if size%2 == 0:
        height = size + 1
        width = height
    else:
        height = size
        width = height

    a = np.ones((height,width),dtype=int)
    r = startPoint(height)
    c = startPoint(width)    
    a[r,c] = 0
    generateMaze(a,r,c,height,width)
    
    a[r,c] = 2
    print(f'maze size = ({height}X{width})')
    print(f'start @ row={r}, column={c}')
    if a[height-r,width-c] == 0:
        a[height-r,width-c] = 3
        print(f'end @ row={height-r}, column={width-c}')
    elif a[height-r,width-(c+1)] == 0:
        a[height-r,width-(c+1)] = 3
        print(f'end @ row={height-r}, column={width-(c+1)}')
    elif a[height-r,width-(c-1)] == 0:
        a[height-r,width-(c-1)] = 3
        print(f'end @ row={height-r}, column={width-(c-1)}')
    elif a[height-(r+1),width-c] == 0:
        a[height-(r+1),width-c] = 3
        print(f'end @ row={height-(r+1)}, column={width-c}')
    elif a[height-(r-1),width-c] == 0:
        a[height-(r-1),width-c] = 3
        print(f'end @ row={height-(r-1)}, column={width-c}')
    else:
        a[height-(r-1),width-(c-1)] = 3
        print(f'end @ row={height-(r-1)}, column={width-(c-1)}')
    print()    
    return a

maze = maze(np.random.randint(64,65,dtype=int))

maze = pd.DataFrame(maze)
maze = maze.replace([0],'')
maze = maze.replace([1],'\u25A0')
maze = maze.replace([2],'S')
maze = maze.replace([3],'X')
maze = maze.to_string()

with open("G:\My Drive\my_mazes.txt", "a", encoding="utf-8") as f:
	f.write(maze)
with open("G:\My Drive\my_mazes.txt", "a", encoding="utf-8") as f:
    f.write('\n')
with open("G:\My Drive\my_mazes.txt", "a", encoding="utf-8") as f:
    f.write('\n')






# %%