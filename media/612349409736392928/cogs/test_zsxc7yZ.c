

#include <stdio.h>



void main ()
{

  int n, i, num[100];
  FILE *optr, *eptr;
  printf("EMMANUEL MAVELY - 696 \n");
  printf ("Enter the limit: ");
  scanf ("%d", &n);
  for (i = 0; i<n; i++)
    scanf ("%d", &num[i]);
  printf ("Separating the numbers into two different files");
  optr = fopen ("odd.txt", "a");
  eptr = fopen ("even.txt", "a");
  for (i = 0; i < n; i++)
    {
      if (num[i] % 2 == 0) 
        fprintf (eptr, "%d", num[i]);
      else
        fprintf (optr, "%d", num[i]);
    }
  fclose (optr);
  fclose (eptr);

}


