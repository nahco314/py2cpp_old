cpp_side_code = """#include<bits/stdc++.h>
#pragma GCC target("avx")
#pragma GCC optimize("O3")
#pragma GCC optimize("unroll-loops")
using namespace std;
template <typename T>bool py_is(const std::vector<T>&a,const std::vector<T>&b){return&a==&b;}
template <typename T>bool py_is(T a, T b){return a==b;}
template <typename T, typename U>bool py_is(T a, U b){return false;}
template <typename T>bool py_in(const std::vector<T>&a,T b){return std::find(a.begin(), a.end(), b) != a.end();}
template <typename T, typename U>bool py_in(const std::vector<T>&a,U b){return false;}

template <template <typename ...> typename C,typename A, typename F>
inline auto transform(const A& v, F&& f)
{
    using result_type
        = C<decltype(std::declval<F>()(std::declval<typename A::value_type>()))>;
    result_type y(v.size());
    std::transform(
        std::cbegin(v),
        std::cend(v),
        std::begin(y),
        f);    
    return y;
}

vector<long long> fill_vec(long long n, long long k){
vector<long long> vec(n, k);
return vec;
}

vector<string> py_split_nostr(string s) {
    int first = 0, last = s.find_first_of(" ");
    vector<string> result = {};
    while(first < int(s.size())){
        string t(s, first, last-first);
        if(t != "")result.push_back(t);
        first = last + 1;
        last = s.find_first_of(" ", first);
        if(last == int(string::npos)) {
            last = s.size();
        }
    }
 
    return result;
}
vector<long long> py_int_split(string s) {
    long long first = 0, last = s.find_first_of(" ");
    vector<long long> result = {};
    while(first < int(s.size())){
        string t(s, first, last-first);
        if(t != ""){         
 result.push_back(stoi(t));
        }
        first = last + 1;
        last = s.find_first_of(" ", first);
          if(last == int(string::npos)) {
            last = s.size();
        }
    }
 
    return result;
}

template<typename T> T py_index(vector<T>&vec, int i){return i >= 0 ? vec[i] : vec[vec.size()+i];}

string py_input(){
string str;
getline(cin, str);
return str;
}

auto py_mod(auto n, auto m){
  return ((n < 0) ^ (m < 0))? m + fmod(n, m) : fmod(n, m);
}

int main(){"""