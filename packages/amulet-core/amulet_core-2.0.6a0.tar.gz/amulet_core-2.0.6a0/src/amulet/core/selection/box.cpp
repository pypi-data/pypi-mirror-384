#include <algorithm>
#include <array>

#include <amulet/utils/matrix.hpp>

#include "box.hpp"
#include "box_group.hpp"
#include "cuboid.hpp"

namespace Amulet {

// Contains and intersects
bool SelectionBox::contains_block(std::int64_t x, std::int64_t y, std::int64_t z) const
{
    return _min_x <= x && x < max_x()
        && _min_y <= y && y < max_y()
        && _min_z <= z && z < max_z();
}
bool SelectionBox::contains_point(double x, double y, double z) const
{
    return _min_x <= x && x <= max_x()
        && _min_y <= y && y <= max_y()
        && _min_z <= z && z <= max_z();
}
bool SelectionBox::contains_box(const SelectionBox& other) const
{
    return _min_x <= other._min_x
        && _min_y <= other._min_y
        && _min_z <= other._min_z
        && other.max_x() <= max_x()
        && other.max_y() <= max_y()
        && other.max_z() <= max_z();
}
bool SelectionBox::intersects(const SelectionBox& other) const
{
    return _min_x < other.max_x() && other._min_x < max_x()
        && _min_y < other.max_y() && other._min_y < max_y()
        && _min_z < other.max_z() && other._min_z < max_z();
}
bool SelectionBox::intersects(const SelectionBoxGroup& other) const
{
    return other.intersects(*this);
}
bool SelectionBox::touches_or_intersects(const SelectionBox& other) const
{
    return _min_x <= other.max_x() && other._min_x <= max_x()
        && _min_y <= other.max_y() && other._min_y <= max_y()
        && _min_z <= other.max_z() && other._min_z <= max_z();
};
bool SelectionBox::touches(const SelectionBox& other) const
{
    return touches_or_intersects(other) && !intersects(other);
}

// Transform
SelectionBox SelectionBox::translate(std::int64_t dx, std::int64_t dy, std::int64_t dz) const
{
    return SelectionBox(
        _min_x + dx,
        _min_y + dy,
        _min_z + dz,
        _size_x,
        _size_y,
        _size_z);
}
SelectionBoxGroup SelectionBox::transform(const Matrix4x4& matrix) const {
    return SelectionCuboid(_min_x, _min_y, _min_z, _size_x, _size_y, _size_z).transform(matrix)->voxelise();
}

std::strong_ordering SelectionBox::operator<=>(const SelectionBox& other) const
{
    return std::tie(
               _min_x,
               _min_y,
               _min_z,
               _size_x,
               _size_y,
               _size_z)
        <=> std::tie(
            other._min_x,
            other._min_y,
            other._min_z,
            other._size_x,
            other._size_y,
            other._size_z);
}
bool SelectionBox::operator==(const SelectionBox& other) const
{
    return std::tie(
               _min_x,
               _min_y,
               _min_z,
               _size_x,
               _size_y,
               _size_z)
        == std::tie(
            other._min_x,
            other._min_y,
            other._min_z,
            other._size_x,
            other._size_y,
            other._size_z);
}

} // namespace Amulet
