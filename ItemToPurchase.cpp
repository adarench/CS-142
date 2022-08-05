//
// Created by Adam Rencher on 3/22/22.
//
#include <string>
using namespace std;

#include "ItemToPurchase.h"


void Groceries::SetPrice(double aPrice) const{
    aPrice = itemPrice;
}
double Groceries::GetPrice(double aPrice){
    return aPrice;
}
void Groceries::SetName(string aName){
    aName = itemName;
}
string Groceries::GetName(string aName){
    return aName;
}
void Groceries::SetQuantity(int aQuantity){
    aQuantity = itemQuantity;
}
int Groceries::GetQuantity(int aQuantity){
    return aQuantity;
}
Groceries::Groceries(){
    itemName = "none";
    itemPrice = 0.0;
    itemQuantity = 0;
}

