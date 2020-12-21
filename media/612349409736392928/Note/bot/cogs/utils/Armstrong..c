// program to print armstrong numbers
// armstrong numbers are numbers which are equal to sum of the cube of its digits.
// 153 = (1*1*1*)+(5*5*5)+(3*3*3) = 153

#include  <stdio.h>

void main (){
	int num, copy, sum, last_digit;
	for (num=100; num<1000; num++)
	{
		sum = 0;
		copy = num;
		while(copy!=0)
		{
		last_digit = copy%10;
		copy /= 10;
		sum += last_digit*last_digit*last_digit;
	    }
	    if(sum==num)
	    printf("%d ", num);
		
	}	
	printf("Are the armstrong numbers");
}	

