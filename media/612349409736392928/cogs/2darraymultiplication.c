

//12. Program to find the sum of digits of a number into a single digit
//
//14. Program to reverse a string using recursion
//
//15. Program to determine the length of a character string using pointer



#include <stdio.h>
//
//
//void reverseChar(){
//	char c;
//	scanf("%c",&c);
//	if(c!='\n')
//	{
//		reverseChar();
//			printf("%c", c);
//	}
//}
//
//
//void main() {
//	printf("Enter a sentance: ");
//	reverseChar();
//}

int get_string_length(char *p)
{
	int count = 0;
	while(*p!='\0')
	{
		p++;
		count++;
	}
	return count;
}

void main ()
{
	char string[20];
	printf("Enter a string: ");
	gets(string);
	printf("String length %d",get_string_length(string));
	
}
