#include <iostream>
#include <iomanip>
#include <cmath>
using namespace std;

double CalcRectanglePerimeter(double & height, double & width);
void PrintRectanglePerimeter(double & height, double & width);
void DoubleRectanglePerimeter(double & height, double & width);

double CalcCircumOfCircle(double & radius);
double CalcAreaOfCircle(double & radius);
double CalcVolumeOfSphere(double & radius);
void SwapNums(int valueA, int valueB);

const double PI = 3.14;

int main(){
   cout << "Getting this line to print earns you points!\n"
   
   double height = 0;
   double width = 0;
   double radius = 0;
   
   cin >> height >> width >> radius;
   
   CalcRectanglePerimeter(height, width);
   cout << PrintRectanglePerimeter(height, width) << endl;
   cout << "... about to double height and width...\n";
   cout << DoubleRectanglePerimeter(width, width) << endl;
  
   
   
   return 0;
}

double CalcRectanglePerimeter(double & height, double & width){
   return ((height + width) * 2);
}
void PrintRectanglePerimeter(double & height, double & width){
   cout << fixed << setprecision(1);
   cout << "A rectangle with height " << height << " and width " << width << " has a perimeter of " << ((height + width) * 2) <<"."<< endl;
}

void DoubleRectanglePerimeter(double & height, double & width){
   height *= 2;
   width *= 2
}

double CalcCircumOfCircle(double & radius){
   return 2*PI*radius;
}
double CalcAreaOfCircle(double & radius){
   return PI*pow(radius, 2);
}
double CalcVolumeOfSphere(double & radius){
   return (4*(PI*pow(radius, 3)))/3;
}

void SwapNums(int & valueA, int & valueB){
   int valueC = valueA;
   valueA = value B;
   valueB = valueA;
}