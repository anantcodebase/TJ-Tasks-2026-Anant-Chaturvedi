#include <iostream>
#include <vector>
#include <climits>

using namespace std;

int main() {
    int n;
    cout<<"Enter The Array Size"<<endl;
    if (!(cin >> n)) return 0;

    long long max1 = LLONG_MIN;
    long long max2 = LLONG_MIN;
    cout<<"Enter The Elements, Separated by Space"<<endl;

    for (int i = 0; i < n; i++) {
        long long x;
        cin >> x;

        if (x > max1) {
            max2 = max1;
            max1 = x;  
        } else if (x < max1 && x > max2) {
            max2 = x;
        }
    }

    if (max2 == LLONG_MIN) {
        cout << -1 << endl;
    } else {
        cout <<"Second Largest Distinct Element Is: "<< max2 << endl;
    }

    return 0;
}
