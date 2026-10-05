// Independent congruence-partition oracle and affine compiler.
// This translation unit is self-contained; no previous round code is included.
#include <algorithm>
#include <array>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>
using namespace std;
constexpr int MAX=80;
const int dx[4]={1,0,-1,0},dy[4]={0,1,0,-1};
const string compass="ENWS";
struct Spec {
 int n,L; vector<int> dirs,phase,w,mask,out; vector<vector<int>> visits;
 Spec(vector<int>d,vector<int>p):n((int)d.size()+1),dirs(d),phase(p){
  if(n<2||n>20||phase.size()!=dirs.size())throw runtime_error("input length");
  vector<pair<int,int>> xy{{0,0}};
  for(int i=0;i<n-1;i++){
   if(dirs[i]<0||dirs[i]>=4||phase[i]<-1||phase[i]>1)throw runtime_error("input symbol");
   if(i&&phase[i]>=0&&phase[i-1]>=0)throw runtime_error("adjacent doubled edges");
   auto [x,y]=xy.back();pair<int,int> q{x+dx[dirs[i]],y+dy[dirs[i]]};
   for(int j=0;j<(int)xy.size();j++){
    int r=abs(q.first-xy[j].first)+abs(q.second-xy[j].second);
    if(r==0||(r==1&&j!=(int)xy.size()-1))throw runtime_error("not an induced path");
   }xy.push_back(q);
  }
  mask.assign(n,0);for(int e=0;e<n-1;e++){mask[e]|=1<<dirs[e];mask[e+1]|=1<<((dirs[e]+2)%4);}
  auto edge=[&](int u,int v,int ph){int e=min(u,v);w.push_back(u);if(phase[e]==ph){w.push_back(v);w.push_back(u);}};
  for(int e=0;e<n-1;e++)edge(e,e+1,0);
  for(int e=n-2;e>=0;e--)edge(e+1,e,1);
  L=w.size();if(L+3>=MAX)throw runtime_error("oracle size limit");visits.resize(n);
  for(int i=0;i<L;i++){visits[w[i]].push_back(i);int v=w[(i+1)%L];out.push_back(v>w[i]?dirs[w[i]]:(dirs[v]+2)%4);}
 }
 string name()const{string s;for(int d:dirs)s+=compass[d];return s;}
 string phases()const{string s;for(int p:phase)s+=(p<0?'-':char('0'+p));return s;}
};
struct DSU{
 array<int,MAX> p;
 DSU(){iota(p.begin(),p.end(),0);}
 int f(int a){while(p[a]!=a){p[a]=p[p[a]];a=p[a];}return a;}
 bool join(int a,int b){a=f(a);b=f(b);if(a==b)return false;if(a>b)swap(a,b);p[b]=a;return true;}
};
struct PartitionOracle{
 const Spec&S;vector<pair<int,int>>neq,eq;vector<int>answer;uint64_t nodes=0;
 explicit PartitionOracle(const Spec&s):S(s){
  for(int i=0;i<S.L;i++)for(int j=i+1;j<S.L;j++)
   if(S.w[i]==S.w[j]||(S.mask[S.w[i]]==S.mask[S.w[j]]&&S.out[i]!=S.out[j]))neq.push_back({i,j});
  for(int a=0;a<3;a++)for(int b=a+1;b<3;b++)neq.push_back({S.L+a,S.L+b});
 }
 bool closure(DSU&d){
  bool changed=true;
  while(changed){
   changed=false;
   for(auto [a,b]:neq)if(d.f(a)==d.f(b))return false;
   int next[MAX][16];fill(&next[0][0],&next[0][0]+MAX*16,-1);
   for(int i=0;i<S.L;i++){
    int r=d.f(i),m=S.mask[S.w[i]],j=(i+1)%S.L;
    if(next[r][m]<0)next[r][m]=j;
    else changed|=d.join(next[r][m],j);
   }
  }
  return true;
 }
 bool dfs(DSU d){
  ++nodes;if(!closure(d))return false;
  int palette[3];for(int a=0;a<3;a++)palette[a]=d.f(S.L+a);
  int forbid[MAX]={};int deg[MAX]={};
  for(auto[a,b]:neq){a=d.f(a);b=d.f(b);deg[a]++;deg[b]++;for(int k=0;k<3;k++){if(a==palette[k])forbid[b]|=1<<k;if(b==palette[k])forbid[a]|=1<<k;}}
  int chosen=-1,choices=8,degree=-1,allow=0;
  for(int i=0;i<S.L;i++){
   int r=d.f(i);if(r==palette[0]||r==palette[1]||r==palette[2])continue;
   int a=7^forbid[r],c=__builtin_popcount((unsigned)a);
   if(c==0)return false;
   if(c<choices||(c==choices&&deg[r]>degree)){chosen=r;choices=c;degree=deg[r];allow=a;}
  }
  if(chosen<0){answer.resize(S.L);for(int i=0;i<S.L;i++)for(int k=0;k<3;k++)if(d.f(i)==palette[k])answer[i]=k;return true;}
  // All three palette choices are retained. Only global color of visit zero is fixed.
  for(int k=0;k<3;k++)if(allow&(1<<k)){DSU e=d;e.join(chosen,S.L+k);if(dfs(e))return true;}
  return false;
 }
 bool solve(){DSU d;d.join(0,S.L);for(auto[a,b]:eq)d.join(a,b);return dfs(d);}
};
struct Lin{
 int n;array<uint64_t,MAX>r{};array<int,MAX>b{};bool good=true;
 explicit Lin(int n0=0):n(n0){}
 bool add(uint64_t a,int c){
  if(!good)return false;
  while(a){int k=63-__builtin_clzll(a);if(r[k]){a^=r[k];c^=b[k];}else{r[k]=a;b[k]=c;return true;}}
  if(c) { good=false; }
  return good;
 }
 uint64_t solution()const{uint64_t z=0;for(int k=0;k<n;k++)if(r[k]&&((__builtin_parityll(r[k]&z)^b[k])!=0))z|=1ULL<<k;return z;}
};
struct Expr{uint64_t a[2]={0,0};int c=0;};
struct AffineCriterion{
 const Spec&S;int m;vector<int>masks,sing,a,kap,forced,ep;vector<int>mi,eps,tv;vector<Expr>X;vector<vector<int>>ug,bg;
 vector<int>answer,profile_s,profile_a,profile_k,profile_ep;uint64_t answer_z=0,branches=0;bool gate=true;
 explicit AffineCriterion(const Spec&s):S(s){
  set<int>ms;for(int v=1;v<S.n-1;v++)ms.insert(S.mask[v]);masks.assign(ms.begin(),ms.end());m=masks.size();
  mi.assign(16,-1);for(int k=0;k<m;k++)mi[masks[k]]=k;
  sing.resize(m);a.resize(m);kap.resize(m);forced.assign(m,-1);ep.assign(S.L,0);eps.resize(S.L);tv.resize(S.L);X.resize(S.L);ug.resize(m);bg.resize(m);
  for(int v=1;v<S.n-1;v++)if(S.visits[v].size()==3){int cnt[4]={};for(int i:S.visits[v])cnt[S.out[i]]++;int one=-1;for(int d=0;d<4;d++)if(cnt[d]==1)one=d;
   int k=mi[S.mask[v]];if(forced[k]>=0&&forced[k]!=one)gate=false;forced[k]=one;
  }
 }
 bool vec(Lin&l,const Expr&u,const Expr&v,int k=0,uint64_t t=0,int ec=0){
  int c=u.c^v.c^(ec?k:0);
  for(int j=0;j<2;j++)if(!l.add(u.a[j]^v.a[j]^(((k>>j)&1)?t:0),(c>>j)&1))return false;
  return true;
 }
 bool kappas(int at,Lin l){
  if(at==m){
   branches++;uint64_t z=l.solution();answer.resize(S.L);
   for(int i=0;i<S.L;i++){int x=X[i].c;for(int j=0;j<2;j++)x^=__builtin_parityll(X[i].a[j]&z)<<j;if(!x)throw runtime_error("zero state");answer[i]=x-1;}
   profile_s=sing;profile_a=a;profile_k=kap;profile_ep=ep;answer_z=z;return true;
  }
  auto&g=bg[at];if(g.size()<=1){kap[at]=(forced[at]<0?0:1);return kappas(at+1,l);}
  for(int k=(forced[at]<0?0:1);k<=3;k++){
   Lin ll=l;bool ok=true;int j=g[0];
   for(size_t h=1;h<g.size()&&ok;h++){
    int i=g[h];uint64_t t=(1ULL<<tv[i])^(1ULL<<tv[j]);
    ok=vec(ll,X[(i+1)%S.L],X[(j+1)%S.L],k,t,eps[i]^eps[j]);
   }
   if(ok){kap[at]=k;if(kappas(at+1,ll))return true;}
  }return false;
 }
 bool compile(){
  for(auto&g:ug) { g.clear(); }
  for(auto&g:bg) { g.clear(); }
  for(int v=0;v<S.n;v++){
   if(v==0||v==S.n-1){for(int i:S.visits[v]){X[i]=Expr();X[i].c=ep[i];}continue;}
   int k=mi[S.mask[v]],e=0,b=1;while(b==a[k])b++;
   for(int i:S.visits[v]){
    X[i]=Expr();
    if(S.out[i]==sing[k]){X[i].c=a[k];ug[k].push_back(i);}
    else{eps[i]=e++;tv[i]=v-1;X[i].c=b^(eps[i]?a[k]:0);for(int j=0;j<2;j++)if((a[k]>>j)&1)X[i].a[j]=1ULL<<(v-1);bg[k].push_back(i);}
   }
  }
  Lin l(S.n-2);
  // Complete global S3 gauge: first internal singleton is 1, its first paired state 2.
  if(S.n>2&&!l.add(1,0))return false;
  for(int k=0;k<m;k++)for(size_t h=1;h<ug[k].size();h++)if(!vec(l,X[(ug[k][0]+1)%S.L],X[(ug[k][h]+1)%S.L]))return false;
  map<pair<int,int>,int> anchors;
  for(int v:{0,S.n-1})for(int i:S.visits[v]){
   auto key=make_pair(S.mask[v],ep[i]);if(anchors.count(key)){if(!vec(l,X[(i+1)%S.L],X[(anchors[key]+1)%S.L]))return false;}else anchors[key]=i;
  }
  return kappas(0,l);
 }
 bool endpoints(int which){
  if(which==2) { return compile(); }
  int v=which==0?0:S.n-1;auto&g=S.visits[v];
  for(int x=1;x<=3;x++){
   if(S.n==2&&which==0&&x!=1) { continue; }
   ep[g[0]]=x;
   if(g.size()==1){if(endpoints(which+1))return true;}
   else for(int y=1;y<=3;y++)if(y!=x){if(S.n==2&&which==0&&y!=2)continue;ep[g[1]]=y;if(endpoints(which+1))return true;}
  }return false;
 }
 bool roles(int at){
  if(at==m)return endpoints(0);
  for(int d=0;d<4;d++)if((masks[at]&(1<<d))&&(forced[at]<0||forced[at]==d)){
   sing[at]=d;for(int x=1;x<=3;x++){
    if(S.n>2&&at==mi[S.mask[1]]&&x!=1) { continue; }
    a[at]=x;if(roles(at+1))return true;
   }
  }return false;
 }
 bool solve(){return gate&&roles(0);}
};
using Table=array<array<pair<int,int>,16>,3>;
bool validate(const Spec&S,const vector<int>&q){
 if((int)q.size()!=S.L) { return false; }
 Table F;for(auto&r:F)for(auto&c:r)c={-1,-1};
 set<pair<int,int>>seen;
 for(int i=0;i<S.L;i++){
  if(q[i]<0||q[i]>=3||!seen.insert({S.w[i],q[i]}).second)return false;
  auto&c=F[q[i]][S.mask[S.w[i]]];pair<int,int>y={S.out[i],q[(i+1)%S.L]};if(c.first>=0&&c!=y)return false;c=y;
 }
 // Complete all 45 rows independently, without using profile parameters.
 for(int q0=0;q0<3;q0++)for(int M=1;M<16;M++)if(F[q0][M].first<0)F[q0][M]={__builtin_ctz((unsigned)M),0};
 int v=S.w[0],state=q[0];set<pair<int,int>>orbit;
 for(int t=0;t<S.L;t++){
  if(v!=S.w[t]||state!=q[t]||!orbit.insert({v,state}).second)return false;
  auto[d,r]=F[state][S.mask[v]];int dest=-1;
  if(v<S.n-1&&S.dirs[v]==d)dest=v+1;
  if(v>0&&(S.dirs[v-1]+2)%4==d)dest=v-1;
  if(dest<0) { return false; }
  v=dest;state=r;
 }
 return v==S.w[0]&&state==q[0];
}
string ints(const vector<int>&v){string s="[";for(size_t i=0;i<v.size();i++){if(i)s+=",";s+=to_string(v[i]);}return s+"]";}
struct Totals{uint64_t count=0,yes=0,gate=0,residual=0,nodes=0,mismatch=0;};
int main(int argc,char**argv){
 try{
  if(argc>=2&&string(argv[1])=="--case"){
   if(argc!=4) { throw runtime_error("--case directions phases"); }
   vector<int>d,p;for(char c:string(argv[2])){auto k=compass.find(c);if(k==string::npos)throw runtime_error("direction");d.push_back(k);}for(char c:string(argv[3]))p.push_back(c=='-'?-1:c-'0');
   Spec S(d,p);PartitionOracle o(S);bool exact=o.solve();AffineCriterion a(S);bool affine=a.solve();
   cout<<"{\"directions\":\""<<S.name()<<"\",\"phases\":\""<<S.phases()<<"\",\"exact\":"<<exact<<",\"affine\":"<<affine<<",\"gate\":"<<a.gate<<",\"word\":"<<ints(S.w)<<",\"mask\":"<<ints(S.mask)<<",\"q_exact\":"<<ints(o.answer)<<",\"q_affine\":"<<ints(a.answer)<<"}\n";
   if(exact!=affine||(exact&&(!validate(S,o.answer)||!validate(S,a.answer)))) { return 2; }
   return 0;
  }
  int maxn=argc>1?stoi(argv[1]):7;string output=argc>2?argv[2]:".";if(maxn<2||maxn>12)throw runtime_error("n in 2..12 required");
  ofstream summary(output+"/fresh_summary.json");if(!summary)throw runtime_error("output directory missing");summary<<"{\"normalization\":\"translation only; all four initial directions; no path reversal quotient\",\"sizes\":[\n";
  for(int n=2;n<=maxn;n++){
   Totals T;uint64_t geometries=0;
   ofstream file(output+"/fresh_n"+to_string(n)+".jsonl");
   vector<pair<int,int>>xy{{0,0}};vector<int>d;
   function<void()> geometry=[&](){
    if((int)xy.size()==n){
     geometries++;vector<int>p(n-1,-1);
     function<void(int)> phases=[&](int e){
      if(e==n-1){
       Spec S(d,p);PartitionOracle O(S);bool ex=O.solve();AffineCriterion A(S);bool af=A.solve();T.count++;T.nodes+=O.nodes;
       if(ex)T.yes++;else if(!A.gate)T.gate++;else T.residual++;
       bool ok=ex==af&&(!ex||(validate(S,O.answer)&&validate(S,A.answer)));
       if(!ok){T.mismatch++;cerr<<"MISMATCH "<<S.name()<<" "<<S.phases()<<endl;}
       file<<"{\"d\":\""<<S.name()<<"\",\"p\":\""<<S.phases()<<"\",\"exact\":"<<ex<<",\"affine\":"<<af<<",\"gate\":"<<A.gate<<",\"oracle_nodes\":"<<O.nodes;
       if(ex)file<<",\"q_exact\":"<<ints(O.answer)<<",\"q_affine\":"<<ints(A.answer)<<",\"masks\":"<<ints(A.masks)<<",\"singleton\":"<<ints(A.profile_s)<<",\"a\":"<<ints(A.profile_a)<<",\"kappa\":"<<ints(A.profile_k)<<",\"endpoint\":"<<ints(A.profile_ep)<<",\"z\":"<<A.answer_z;
       file<<"}\n";
       return;
      }
      p[e]=-1;phases(e+1);
      if(e==0||p[e-1]<0) { for(int bit=0;bit<2;bit++){p[e]=bit;phases(e+1);} }
      p[e]=-1;
     };phases(0);return;
    }
    for(int k=0;k<4;k++){
     auto[x,y]=xy.back();pair<int,int>q{x+dx[k],y+dy[k]};bool ok=true;
     for(int j=0;j<(int)xy.size();j++){int dist=abs(q.first-xy[j].first)+abs(q.second-xy[j].second);if(dist==0||(dist==1&&j!=(int)xy.size()-1)){ok=false;break;}}
     if(ok){xy.push_back(q);d.push_back(k);geometry();d.pop_back();xy.pop_back();}
    }
   };geometry();
   string row="{\"n\":"+to_string(n)+",\"geometries\":"+to_string(geometries)+",\"specifications\":"+to_string(T.count)+",\"realizable\":"+to_string(T.yes)+",\"direction_rejections\":"+to_string(T.gate)+",\"residual_rejections\":"+to_string(T.residual)+",\"oracle_nodes\":"+to_string(T.nodes)+",\"mismatches\":"+to_string(T.mismatch)+"}";
   summary<<(n>2?",\n":"")<<row;summary.flush();cerr<<row<<endl;
   if(T.mismatch){summary<<"]}\n";return 2;}
  }summary<<"\n]}\n";
 }catch(const exception&e){cerr<<e.what()<<endl;return 1;}return 0;
}
