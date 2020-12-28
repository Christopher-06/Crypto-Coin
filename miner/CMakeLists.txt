cmake_minimum_required(VERSION 2.4)

project(cryptocoin_miner)
include_directories(${PROJECT_SOURCE_DIR})


include(FetchContent)
FetchContent_Declare(cpr GIT_REPOSITORY https://github.com/whoshuu/cpr.git GIT_TAG c8d33915dbd88ad6c92b258869b03aba06587ff9) # the commit hash for 1.5.0
FetchContent_MakeAvailable(cpr)


FetchContent_Declare(json
  GIT_REPOSITORY https://github.com/nlohmann/json.git
  GIT_TAG v3.7.3)

FetchContent_GetProperties(json)
if(NOT json_POPULATED)
  FetchContent_Populate(json)
  add_subdirectory(${json_SOURCE_DIR} ${json_BINARY_DIR} EXCLUDE_FROM_ALL)
endif()

add_executable(miner main.cpp block.cpp sha256.cpp)
target_link_libraries(miner PRIVATE nlohmann_json::nlohmann_json)
target_link_libraries(miner PRIVATE cpr::cpr)