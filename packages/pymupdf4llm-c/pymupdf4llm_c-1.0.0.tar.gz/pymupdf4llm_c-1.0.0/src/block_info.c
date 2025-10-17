#include "block_info.h"

#include <math.h>
#include <stdlib.h>
#include <string.h>

const char* block_type_to_string(BlockType t)
{
    switch (t)
    {
    case BLOCK_PARAGRAPH:
        return "paragraph";
    case BLOCK_HEADING:
        return "heading";
    case BLOCK_TABLE:
        return "table";
    case BLOCK_LIST:
        return "list";
    case BLOCK_FIGURE:
        return "figure";
    default:
        return "other";
    }
}

void block_array_init(BlockArray* arr)
{
    if (!arr)
        return;
    arr->items = NULL;
    arr->count = 0;
    arr->capacity = 0;
}

void block_array_free(BlockArray* arr)
{
    if (!arr)
        return;
    for (size_t i = 0; i < arr->count; ++i)
    {
        free(arr->items[i].text);
    }
    free(arr->items);
    arr->items = NULL;
    arr->count = 0;
    arr->capacity = 0;
}

BlockInfo* block_array_push(BlockArray* arr)
{
    if (!arr)
        return NULL;
    if (arr->count == arr->capacity)
    {
        size_t new_cap = arr->capacity == 0 ? 32 : arr->capacity * 2;
        BlockInfo* tmp = (BlockInfo*)realloc(arr->items, new_cap * sizeof(BlockInfo));
        if (!tmp)
            return NULL;
        arr->items = tmp;
        arr->capacity = new_cap;
    }
    BlockInfo* info = &arr->items[arr->count++];
    memset(info, 0, sizeof(BlockInfo));
    return info;
}

int compare_block_position(const void* a, const void* b)
{
    const BlockInfo* ia = (const BlockInfo*)a;
    const BlockInfo* ib = (const BlockInfo*)b;

    float dy = ia->bbox.y0 - ib->bbox.y0;
    if (fabsf(dy) > 1e-3f)
    {
        return (dy < 0.0f) ? -1 : 1;
    }

    float dx = ia->bbox.x0 - ib->bbox.x0;
    if (fabsf(dx) > 1e-3f)
    {
        return (dx < 0.0f) ? -1 : 1;
    }

    return 0;
}
