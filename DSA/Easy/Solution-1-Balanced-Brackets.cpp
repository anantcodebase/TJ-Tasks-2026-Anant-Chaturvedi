#include <iostream>
#include <string>
#include <stack>

using namespace std;

string isBalanced(string s) {
    stack<char> st;
    
    for (char ch : s) {
        if (ch == '(' || ch == '{' || ch == '[') {
            st.push(ch);
        } else {
            if (st.empty()) return "NO";
            
            char top = st.top();
            if ((ch == ')' && top == '(') ||
                (ch == '}' && top == '{') ||
                (ch == ']' && top == '[')) {
                st.pop();
            } else {
                return "NO";
            }
        }
    }
    
    return st.empty() ? "YES" : "NO";
}

int main() {
    string s;
    if (cin >> s) {
        cout <<"The answer is " << isBalanced(s) << endl;
    }
    return 0;
}  
