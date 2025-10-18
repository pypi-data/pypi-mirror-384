////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include <cereal/archives/portable_binary.hpp>
#include <cereal/types/array.hpp>
#include <cereal/types/complex.hpp>
#include <cereal/types/optional.hpp>
#include <cereal/types/string.hpp>
#include <cereal/types/tuple.hpp>
#include <cereal/types/vector.hpp>

#include <fstream>
#include <memory>
#include <string_view>

namespace hem::Serialize {

namespace detail {

// An RAII-style serializer. Two types supported: `InputSerializer` and
// `OutputSerializer`. Be cautious that the serializion happens only when the
// serializer is out-of-scope.
template <class ArchType, class Stream> class Serializer {
public:
    Serializer(Stream &s) : arch_(s) {}

    template <class... Types> auto &operator()(Types &&...args) {
        arch_(std::forward<Types>(args)...);
        return *this;
    }

private:
    ArchType arch_;
};

} // namespace detail

/*!
A helper class to be used in serialization.
Serialize the constructor's arguments `args` to `ar` when saving. When loading,
on the other hand, check if the loaded values are same with the `args`.
Usage:

void serialize(Archive& ar) {
    ar(Verifier(some_expression_to_check, ...), some_other_members);
}

!*/
template <class... Args> class Verifier {
public:
    template <class... U>
    Verifier(U &&...args) : temporal_arguments_(std::forward<U>(args)...) {}

    template <class Archive> void save(Archive &ar) const {
        std::apply(ar, temporal_arguments_);
    }

    template <class Archive> void load(Archive &ar) const {
        // Deserialize to args and compare with temporal_arguments.
        std::tuple<Args...> args;
        { std::apply(ar, args); }
        if (args != temporal_arguments_) {
            throw std::runtime_error("[Verifier::load] Validation failed "
                                     "during deserializing objects.");
        }
    }

private:
    std::tuple<Args...> temporal_arguments_;
};

// Enable forwarding reference on class template via template deduction guide
template <typename... Us> Verifier(Us &&...) -> Verifier<Us...>;

// Additional, for g++ < 10.2. See
// https://gcc.gnu.org/bugzilla/show_bug.cgi?id=80438
template <typename U, typename... Us> Verifier(U, Us...) -> Verifier<U, Us...>;

// Serialize `args` to `ar` when saving.
// When loading, on the other hand, check if the loaded values are same with
// `args`.
template <class Archive, class... Args>
void Verify(Archive &ar, Args &&...args) {
    Serialize::Verifier verifier(std::forward<Args>(args)...);
    ar(verifier);
}

template <class... Args> void save(std::ostream &stream, Args &&...args) {
    using OutputSerializer =
        detail::Serializer<cereal::PortableBinaryOutputArchive, std::ostream>;
    OutputSerializer arch(stream);
    arch(std::forward<Args>(args)...);
}

template <class... Args> void save(const std::string &path, Args &&...args) {
    std::ofstream file(path, std::ios::binary);
    if (!file.is_open())
        throw std::runtime_error("Cannot open file " + path);
    save(file, std::forward<Args>(args)...);
}

template <class... Args> void load(std::istream &stream, Args &&...args) {
    using InputSerializer =
        detail::Serializer<cereal::PortableBinaryInputArchive, std::istream>;
    InputSerializer arch(stream);
    arch(std::forward<Args>(args)...);
}

template <class... Args> void load(const std::string &path, Args &&...args) {
    std::ifstream file(path, std::ios::binary);
    if (!file.is_open())
        throw std::runtime_error("Cannot open file " + path);
    load(file, std::forward<Args>(args)...);
}

} // namespace hem::Serialize
