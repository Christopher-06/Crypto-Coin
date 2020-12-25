#include <string>
#include <random>
#include <limits.h>

class Block {
public:
	unsigned char* content;
	unsigned int contentLenght;
	unsigned int blockID;
	unsigned int NoncePlacement;

	Block(std::string& json);
	void toString(std::string& output);

	int find(const std::string& pattern);
	bool replace(const std::string& from, const std::string& to, std::string& output);
	void setNonce(unsigned char*& newContent, unsigned int& nonce, unsigned int& contentLen);
};