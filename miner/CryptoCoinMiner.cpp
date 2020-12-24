#include <iostream>
#include <string.h>
#include <chrono>
#include <thread>
#include <random>
#include <limits.h>
#include <regex>
#include <vector>

#include <cpr/cpr.h>

#include <nlohmann/json.hpp>
#include "sha256.h"

using json = nlohmann::json;
using namespace std;

const string MINER_URL = "http://192.168.178.13:8000";
const string GET_PENDING_URL = MINER_URL + "/get/pending";
const string SET_NONCE_URL = MINER_URL + "/set/nonce?nonce=";

const unsigned const int const NTHREADS = thread::hardware_concurrency();
vector<thread> miningThreads;

int Solutions[] = { -1 };
string current_block = "";
string CurrentBlockID = "";
bool mining = false;

double average_hashes_per_sec = 0;
int CorrectNoncesSubmitted = 0;

bool replace(string& str, const string& from, const string& to) {
    size_t start_pos = str.find(from);
    if (start_pos == string::npos)
        return false;
    str.replace(start_pos, from.length(), to);
    return true;
}

void mine() {
    // Randomizer
    random_device rd;
    mt19937 rng(rd());
    uniform_int_distribution<int> uni(0, INT_MAX);

    int times = 0;
    auto t_start = chrono::high_resolution_clock::now();

    int nonce = 0;
    string output = "", input = "";
    while (true) {
        // Test if something is to do
        while (mining == false || current_block == "") {
            if (times != 0) {
                // Calc hashes/sec
                auto t_end = chrono::high_resolution_clock::now();
                double elapsed_time_ms = chrono::duration<double, milli>(t_end - t_start).count();
                double hashes_per_sec = double(times * 1000 / elapsed_time_ms) * (NTHREADS - 1); // Every Mining Thread do this

                if (average_hashes_per_sec == 0)
                    average_hashes_per_sec = hashes_per_sec;
                else {
                    // Calc average
                    average_hashes_per_sec += hashes_per_sec;
                    average_hashes_per_sec /= 2;
                }
            }

            t_start = std::chrono::high_resolution_clock::now();
            times = 0;
        }

        input = current_block;
        ++times;
        nonce = uni(rng);   
        replace(input, "10101010", to_string(nonce));

        output = sha256(input);

        // Test if correct
        if (output.find("c000") == 0)
            Solutions[0] = nonce;
    }
}

int main()
{
    // Start all possible threads
    // -1, because this thread is also running
    for(int i = 1; i < NTHREADS;i ++)
        miningThreads.push_back(thread(mine));

    cout << "Start Mining at: " << MINER_URL << endl;
    cout << "---------------------------------------------------------------" << endl;
    while (true) {
        cpr::Response r = cpr::Get(cpr::Url{ GET_PENDING_URL });

        if (r.status_code != 200) {
            // Something went wrong
            mining = false;
            cout << "\r HTTP Status Code " << r.status_code << ". Trying later again..." << "                                " << flush;
            this_thread::sleep_for(100ms);
            continue;
        }
        else {
            // Parse json
            json doc = json::parse(r.text);
            if (doc.contains("status")) {
                // Waiting
                mining = false;
                cout << "\r Server Response: status=" << doc["status"];
                if (average_hashes_per_sec != 0)
                    cout << "   - KHashes/Sec: " << double(average_hashes_per_sec / 1000);
                if(CorrectNoncesSubmitted != 0)
                    cout << "   - Correct Nonces: " << CorrectNoncesSubmitted;
                cout << "             ";

                this_thread::sleep_for(100ms);
                continue;
            }

            // Have a job
            string block = regex_replace(string(r.text).data(), regex(" "), "");
            current_block = regex_replace(block, regex("\n"), "");

            CurrentBlockID = to_string(doc["id"]);
            mining = true;
        }

        cout << "\r Calculating Hash: ID=" << CurrentBlockID << "     - " << average_hashes_per_sec << "h/s                               " << flush;


        if (mining == true) {
            if (Solutions[0] != -1) {
                continue;
                // Test solution
                r = cpr::Get(cpr::Url{ SET_NONCE_URL + to_string(Solutions[0]) });
                Solutions[0] = -1;

                if (r.status_code == 200) {
                    // Correnct
                    cout << "\r Got correct Nonce! Good job" << "                                   " << flush;
                    mining = false;
                    ++CorrectNoncesSubmitted;
                    this_thread::sleep_for(1000ms);
                }
            }
        }
    }
    return 0;
}
