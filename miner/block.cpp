#include "block.h"
#include <regex>
#include <stdlib.h> 
#include <stdio.h>
#include <random>
#include <limits.h>

using namespace std;

Block::Block() {
	content = new unsigned char[5];
	contentLenght = 5;
	for (unsigned int i = 0; i < contentLenght; ++i)
	{
		// Fill all places
		*(content + i) = NULL;
	}

	mining = false;
	blockID = 0;
	NoncePlacement = find("10101010");
}

Block::Block(string& json) {
	// Preprocess json
	json = regex_replace(json, regex(" "), "");
	json = regex_replace(json, regex("\n"), "");

	// +5 to allocate memory for later nonce setting
	content = new unsigned char[json.length() + 5];
	contentLenght = json.length() + 5;
	for (unsigned int i = 0; i < contentLenght; ++i)
	{
		// Fill all places
		if(i < json.length())
			*(content + i) = json[i];
		else
			*(content + i) = NULL;
	}	

	mining = false;
	blockID = 0;
	NoncePlacement = find("10101010");
}

Block::Block(const char* text, const unsigned int textLen) {
	// +5 to allocate memory for later nonce setting
	content = new unsigned char[textLen + 5];
	contentLenght = textLen + 5;
	for (unsigned int i = 0; i < contentLenght; ++i)
	{
		// Fill all places
		if (i < textLen)
			*(content + i) = *(text + i);
		else
			*(content + i) = NULL;
	}

	mining = false;
	blockID = 0;
	NoncePlacement = find("10101010");
}

Block::~Block() {
	//delete[] content;
}

void Block::toString(string& output) {
	output = string((char*)content);	
}

int Block::find(const string& pattern) {
	unsigned int patternScore = 0;

	if (pattern.length() > contentLenght)
		return string::npos;

	for (unsigned int i = 0; i < contentLenght; ++i) {
		if (*(content + i) == pattern[patternScore])
			++patternScore;
		else
			patternScore = 0;

		if (patternScore == pattern.length())
			return (i - patternScore + 1);
	}

	return string::npos;
}

bool Block::replace(const string& from, const string& to, string& output) {
	size_t start_pos = find(from);
	if (start_pos == string::npos)
		return false;

	char* newContent = new char[contentLenght];
	for (unsigned int i = start_pos; i < (start_pos + to.length()); ++i)
		newContent[i] = to[i - start_pos];


	for (unsigned int i = 0, j = 0; i < contentLenght; ++i, ++j) {
		if (i == start_pos){
			i += to.length();
			j += from.length();
		}

		if (i != start_pos)
			*(newContent + i) = *(content + j);
	}

	output = string(newContent);
	return true;
}

unsigned int NumDigits(int x)
{
	// Fastest way
	x = abs(x);
	return (x < 10 ? 1 :
		(x < 100 ? 2 :
			(x < 1000 ? 3 :
				(x < 10000 ? 4 :
					(x < 100000 ? 5 :
						(x < 1000000 ? 6 :
							(x < 10000000 ? 7 :
								(x < 100000000 ? 8 :
									(x < 1000000000 ? 9 :
										10)))))))));
}

void Block::setNonce(unsigned char*& newContent, unsigned int& nonce, unsigned int& contentLen) {
	// Random Nonce
	if (nonce <= 0) {
		random_device rd;
		mt19937 rng(rd());
		uniform_int_distribution<int> uni(0, INT_MAX);
		nonce = uni(rng);
	}

	// Convert Nonce to char*
	char buffer[128];
	int ret = snprintf(buffer, sizeof(buffer), "%ld", nonce);
	unsigned char* to = (unsigned char*)buffer;

	unsigned int nonceLen = NumDigits(nonce);
	contentLen = contentLenght - 13 + nonceLen;

	// Replace
	unsigned char* pointer_new = (newContent + NoncePlacement);
	for (unsigned int i = 0; i < nonceLen; ++i) {
		*(pointer_new) = to[i];
		++pointer_new;
	} 



	pointer_new = newContent;
	unsigned char* pointer_old = content;
	for (unsigned int i = 0; i < contentLenght; ++i) {
		if (i == NoncePlacement) {
			pointer_new += nonceLen;
			pointer_old += 8; //10101010
		}
		*pointer_new = *pointer_old;

		++pointer_new;
		++pointer_old;
	}
}

