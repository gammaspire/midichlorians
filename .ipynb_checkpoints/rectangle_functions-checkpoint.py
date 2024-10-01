import numpy as np
from scipy import spatial

class rectangle():
    
    #initiate class variables (which I will need for the tkinker gui)
    def __init__(self, angle=None, x_one=None, x_two=None, y_one=None, y_two=None):
        
        self.angle = angle
        self.x_one = x_one
        self.x_two = x_two
        self.y_one = y_one
        self.y_two = y_two
    
    
    #define linear function
    def func(self,x,m,b):
        return m*x+b
    
    
    #from https://stackoverflow.com/questions/34372480/rotate-point-about-another-point-in-degrees-python
    #rotates point according to input angle; outputs rotated points rounded to nearest 0.01
    def rotate(self, point_to_be_rotated, center_point = (0,0)):
        angle_rad = self.angle*np.pi/180
        xnew = np.cos(angle_rad)*(point_to_be_rotated[0] - center_point[0]) - np.sin(angle_rad)*(point_to_be_rotated[1] - center_point[1]) + center_point[0]
        ynew = np.sin(angle_rad)*(point_to_be_rotated[0] - center_point[0]) + np.cos(angle_rad)*(point_to_be_rotated[1] - center_point[1]) + center_point[1]

        return (round(xnew,2),round(ynew,2))
    
    
    #extract x and y vertex coordinates, and the slope of the lines connecting these points
    #this function "returns" lists of (x,y) vertices, and the slopes of the rectangle perimeter lines
    #NOTE: I choose np.max(x)-np.min(x) as the number of elements comprising each equation. seems fine.
    def get_xym(self, event_bounds):
        
        #self.event_bounds contains the list [self.x1,self.y1,self.x2,self.y2]
        self.p1 = [event_bounds[0],event_bounds[1]]   #coordinates of first click event
        self.p2 = [event_bounds[2],event_bounds[3]]   #coordinates of second click event
        
        if self.angle%90 != 0:      #if angle is not divisible by 90, can rotate using this algorithm. 
                        
            n_spaces = int(np.abs(self.p1[0] - self.p2[0]))   #number of 'pixels' between x coordinates
            
            (xc,yc) = ((self.p1[0]+self.p2[0])/2, (self.p1[1]+self.p2[1])/2)
            one_rot = self.rotate(point_to_be_rotated = self.p1, center_point = (xc,yc))
            two_rot = self.rotate(point_to_be_rotated = self.p2, center_point = (xc,yc))
            three_rot = self.rotate(point_to_be_rotated = (self.p1[0],self.p2[1]), center_point = (xc,yc))
            four_rot = self.rotate(point_to_be_rotated = (self.p2[0],self.p1[1]), center_point = (xc,yc))

            x1 = np.linspace(one_rot[0],three_rot[0],n_spaces)
            m1 = (one_rot[1] - three_rot[1])/(one_rot[0] - three_rot[0])
            y1 = three_rot[1] + m1*(x1 - three_rot[0])

            x2 = np.linspace(one_rot[0],four_rot[0],n_spaces)
            m2 = (one_rot[1] - four_rot[1])/(one_rot[0] - four_rot[0])
            y2 = four_rot[1] + m2*(x2 - four_rot[0])

            x3 = np.linspace(two_rot[0],three_rot[0],n_spaces)
            m3 = (two_rot[1] - three_rot[1])/(two_rot[0] - three_rot[0])
            y3 = two_rot[1] + m3*(x3 - two_rot[0])

            x4 = np.linspace(two_rot[0],four_rot[0],n_spaces)
            m4 = (two_rot[1] - four_rot[1])/(two_rot[0] - four_rot[0])
            y4 = two_rot[1] + m4*(x4 - two_rot[0])

            self.x_rot = [x1,x2,x3,x4]
            self.y_rot = [y1,y2,y3,y4]
            self.m_rot = [m1,m2,m3,m4]
            self.n_spaces = n_spaces
            
            self.one_rot = one_rot
            self.two_rot = two_rot
            self.three_rot = three_rot
            self.four_rot = four_rot

        elif (self.angle/90)%2 == 0:  #if angle is divisible by 90 but is 0, 180, 360, ..., no change to rectangle
            
            n_spaces = int(np.abs(self.p1[0] - self.p2[0]))   #number of 'pixels' between x coordinates
            
            x1 = np.zeros(50)+self.p1[0]
            y1 = np.linspace(self.p2[1],self.p1[1],n_spaces)

            x2 = np.linspace(self.p1[0],self.p2[0],n_spaces)
            y2 = np.zeros(50)+self.p2[1]

            x3 = np.linspace(self.p2[0],self.p1[0],n_spaces)
            y3 = np.zeros(50)+self.p1[1]

            x4 = np.zeros(50)+self.p2[0]
            y4 = np.linspace(self.p1[1],self.p2[1],n_spaces)

            self.x_rot = [x1,x2,x3,x4]
            self.y_rot = [y1,y2,y3,y4]
            self.m_rot = [0,0,0,0]
            self.n_spaces = n_spaces
            
            self.one_rot = self.p1
            self.two_rot = self.p2
            self.three_rot = (self.p1[0],self.p2[1])
            self.four_rot = (self.p2[0],self.p1[1])

            
    #get xmin, xmax, ymin, ymax values
    def get_minmax(self, event_bounds, im_length):
        
        try:
            #for the case where the angle is not rotated
            if self.angle == 0:
                
                self.xmin = int(event_bounds[2]) if (event_bounds[0]>event_bounds[2]) else int(event_bounds[0])
                self.xmax = int(event_bounds[0]) if (event_bounds[0]>event_bounds[2]) else int(event_bounds[2])
                self.ymin = int(event_bounds[3]) if (event_bounds[1]>event_bounds[3]) else int(event_bounds[1])
                self.ymax = int(event_bounds[1]) if (event_bounds[1]>event_bounds[3]) else int(event_bounds[3])
            
            #if rectangle is rotated, use rotated coordinates to find mins and maxs
            else:
                xvertices=np.array([self.one_rot[0], self.two_rot[0], self.three_rot[0], self.four_rot[0]])
                yvertices=np.array([self.one_rot[1] ,self.two_rot[1], self.three_rot[1], self.four_rot[1]])
                
                self.xmin = np.min(xvertices)
                self.xmax = np.max(xvertices)
                
                self.ymin = np.min(yvertices)
                self.ymax = np.max(yvertices)
                
        except:
            print('Defaulting to image parameters for xmin, xmax; ymin, ymax.')
            self.xmin=0
            self.xmax=im_length
            self.ymin = int(im_length/2-(0.20*im_length))
            self.ymax = int(im_length/2+(0.20*im_length))
     
    
    #generates lists of line/bar values, means, AND line pixel coordinates. sehr wichtig.
    def get_line_vals(self, dat, event_bounds):
        
        if self.angle == 0:
            cropped_data = dat[self.ymin:self.ymax, self.xmin:self.xmax]   #[rows,columns]; isolates pixels within the user-defined region
            self.mean_strip_values = []   #create empty array for mean px values of the strips
            vertical_lines = [cropped_data[:, i] for i in range(self.xmax-self.xmin)]
            
            #creating list of vertical strip coordinates (will need for animation!)
            x_coords = np.arange(self.xmin,self.xmax,1)
            y_coords = np.arange(self.ymin,self.ymax,1)
            self.all_line_coords = []
            for i in range(self.xmax-self.xmin):
                x = np.zeros(len(y_coords))+x_coords[i]
                y = y_coords
                self.all_line_coords.append(list(zip(np.ndarray.tolist(np.round(x,3)),
                                                np.ndarray.tolist(np.round(y,3)))))
            
            #creating mean strip values from the vertical line pixel values
            for line in vertical_lines:
                self.mean_strip_values.append(np.mean(line))
            
            #need this for later
            self.mean_list = self.mean_strip_values
        
        elif self.angle != 0:
            self.RecRot(dat, event_bounds)
            self.mean_strip_values = self.mean_list
    
    
    #function which outputs rotated coordinate values
    def RecRot(self,dat,event_bounds):
    
        self.get_xym(event_bounds)   #defines and initiates self.x_rot, self.y_rot, self.m_rot
                
        #create lists
        list_to_mean = []
        self.mean_list = []   #only need to initialize once
        self.all_line_coords = []   #also only need to initialize once --> will give x,y coordinates for every line
                                    #(hence the variable name).
        
        
        for i in range(self.n_spaces):  #for the entire n_spaces extent: 
                                        #find x range of between same-index points on opposing sides of the 
                                        #rectangle, determine the equation variables to 
                                        #connect these elements within this desired x range, 
                                        #then find this line's mean pixel value. 
                                        #proceed to next set of elements, etc.

            #points from either x4,y4 (index=3) or x1,y1 (index=0)
            #any angle which is NOT 0,180,360,etc.
            if self.angle%90 != 0:
                self.all_bars = np.zeros(self.n_spaces**2).reshape(self.n_spaces,self.n_spaces)
                xpoints = np.linspace(self.x_rot[3][i],self.x_rot[0][-(i+1)],self.n_spaces)
                b = self.y_rot[0][-(i+1)] - (self.m_rot[2]*self.x_rot[0][-(i+1)])
                ypoints = self.func(xpoints,self.m_rot[2],b)
                
                #convert xpoint, ypoint to arrays, round all elements to 2 decimal places, convert back to lists
                self.all_line_coords.append(list(zip(np.ndarray.tolist(np.round(np.asarray(xpoints),3)),
                                                np.ndarray.tolist(np.round(np.asarray(ypoints),3)))))
                
                for n in range(len(ypoints)):
                    #from the full data grid x, isolate all of values occupying the rows (xpoints) in 
                    #the column ypoints[n]
                    list_to_mean.append(dat[int(ypoints[n])][int(xpoints[n])])

                self.mean_list.append(np.mean(list_to_mean))
                list_to_mean = []
            
            #0,180,360,etc.
            if (self.angle/90)%2 == 0:
                xpoints = np.linspace(self.x_rot[3][i],self.x_rot[0][-(i+1)],self.n_spaces)
                b =self.y_rot[0][-(i+1)] - (self.m_rot[2]*self.x_rot[0][-(i+1)])
                ypoints = self.func(xpoints,self.m_rot[2],b)
                
                #convert xpoint, ypoint to arrays, round all elements to 2 decimal places, convert back to lists
                self.all_line_coords.append(list(zip(np.ndarray.tolist(np.round(np.asarray(xpoints),3)),
                                                np.ndarray.tolist(np.round(np.asarray(ypoints),3)))))
                
                for n in range(len(ypoints)):
                    #from the full data grid x, isolate all of values occupying the rows (xpoints) in 
                    #the column ypoints[n]
                    list_to_mean.append(dat[int(ypoints[n])][int(xpoints[n])])

                self.mean_list.append(np.mean(list_to_mean))
                list_to_mean = []
            
        #check if all_line_coords arranged from left to right
        #if not, sort it (flip last list to first, etc.) and reverse mean_list accordingly
        #first define coordinates of first and second "starting coordinates"
        first_coor = self.all_line_coords[0][0]
        second_coor = self.all_line_coords[1][0]
        
        #isolate the x values
        first_x = first_coor[0]
        second_x = second_coor[0]
        
        #if the first x coordinate is greater than the second, then all set. 
        #otherwise, lists arranged from right to left. fix.
        #must also flip mean_list so that the values remain matched with the correct lines
        if first_x<second_x:
            self.all_line_coords.sort()
            self.mean_list.reverse()
            
            
    #it may not be the most efficient function, as it calculates the distances between every line coordinate and the given (x,y); however, I am not clever enough to conjure up an alternative solution presently.
    def find_closest_bar(self, x_coord, y_coord):
        
        #initiate distances list --> for a given (x,y), which point in every line in self.all_line_coords
        #is closest to (x,y)? this distance will be placed in the distances list.
        self.distances=[]
        
        coord=(x_coord, y_coord)
        
        for line in self.all_line_coords:
            tree = spatial.KDTree(line)
            result=tree.query([coord])
            self.distances.append(result[0])
        
        self.closest_line_index = np.where(np.asarray(self.distances)==np.min(self.distances))[0][0]
        return self.closest_line_index
    
    
    #from the list of means, find the index at which the element is closest in value to the given mean pixel
    def find_closest_mean(self,meanlist,input_mean_px):
        #https://stackoverflow.com/questions/12141150/from-list-of-integers-get-number-closest-to-a-given-value
        self.closest_mean_index = np.where(np.asarray(meanlist) == min(meanlist, key=lambda x:abs(x-float(input_mean_px))))[0][0]     
        