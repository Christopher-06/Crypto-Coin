#include <iostream>
#include <string.h>
#include <chrono>
#include <thread>
#include <random>
#include <limits.h>
#include <regex>
#include <vector>
#include <fstream>

#include <cpr/cpr.h>

#include <nlohmann/json.hpp>
#include "sha256.h"
#include "block.h"

using json = nlohmann::json;
using namespace std;

string MINER_URL = "", GET_PENDING_URL = "", SET_NONCE_URL = "";
const unsigned const int const NTHREADS = thread::hardware_concurrency();
vector<thread> miningThreads;

int Solutions[] = { -1 };

double average_hashes_per_sec = 0;
unsigned int CorrectNoncesSubmitted = 0;

void mine(Block& currentBlock) {
    // Randomizer
    random_device rd;
    mt19937 rng(rd());
    uniform_int_distribution<int> uni(0, INT_MAX);

    // Statistic
    unsigned int times = 0;
    auto t_start = chrono::high_resolution_clock::now();

    unsigned int nonce = 0;
    unsigned int contentLen;
    unsigned char* content = new unsigned char[2000];
    while (true) {
        // Test if something is to do
        while (currentBlock.mining == false) {
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

        // Calc hash with Random Nonce
        ++times;
        nonce = uni(rng);
        currentBlock.setNonce(content, nonce, contentLen);

        if (sha256(content, contentLen))
            Solutions[0] = nonce;
    }
}

int main(int argc, char* argv[])
{      
    if (argc != 2) {
        // Programname, Node Address
        cout << "You have to enter a Node Address as an start Argument. Read the Docs for more information..." << endl;
        return 1;
    }

    Block currentBlock("Hello", 5);
    MINER_URL = argv[1];
    GET_PENDING_URL = MINER_URL + "/get/pending";
    SET_NONCE_URL = MINER_URL + "/set/nonce?nonce=";

    // Start all possible threads  
    for (unsigned int i = 1; i < NTHREADS; ++i)
    {
        // -1, because this thread is also running
        miningThreads.push_back(thread(mine, ref(currentBlock)));
    }

    cout << "Start Mining at: " << MINER_URL << endl;
    cout << "--------------------------------------------------------------------" << endl;
    while (true) {
        cpr::Response r = cpr::Get(cpr::Url{ GET_PENDING_URL });

        if (r.status_code != 200) {
            // Something went wrong
            currentBlock.mining = false;
            cout << "\r HTTP Status Code " << r.status_code << ". Trying later again..." << "                                      " << flush;
            this_thread::sleep_for(100ms);
            continue;
        }
        else {
            // Parse json
            json doc = json::parse(r.text);
            if (doc.contains("status")) {
                // Waiting
                currentBlock.mining = false;
                cout << "\r Server Response: status=" << doc["status"];
                if (average_hashes_per_sec != 0)
                    cout << "   - KHashes/Sec: " << double(average_hashes_per_sec / 1000);
                if (CorrectNoncesSubmitted != 0)
                    cout << "   - Correct Nonces: " << CorrectNoncesSubmitted;
                cout << "                         ";

                this_thread::sleep_for(100ms);
                continue;
            }

            // Have a job
            currentBlock = Block(r.text);
            currentBlock.mining = true;
            currentBlock.blockID = doc["id"];
        }

        cout << "\r Calculating Hash: ID=" << currentBlock.blockID << "     - " << double(average_hashes_per_sec / 1000) << " kh/s                                     " << flush;


        if (currentBlock.mining == true) {
            if (Solutions[0] != -1) {
                // Test solution
                r = cpr::Get(cpr::Url{ SET_NONCE_URL + to_string(Solutions[0]) });
                Solutions[0] = -1;

                if (r.status_code == 200) {
                    // Correnct
                    cout << "\r Got correct Nonce! Good job" << "                                         " << flush;
                    currentBlock.mining = false;
                    ++CorrectNoncesSubmitted;
                    this_thread::sleep_for(1000ms);
                }
            }
        }
    }
    return 0;
}
