/**
 * @file sink.h
 *
 * Defines classes for log sinks (i.e. outputs)
 */

#pragma once

#include <ostream>
#include <fstream>

namespace l3pp {

/**
 * Base class for a logging sink. It can only log some log entry to which some
 * formatting is applied (see Formatter).
 */
class Sink {
	FormatterPtr formatter;

public:
	Sink() : formatter(std::make_shared<Formatter>()) {

	}
	Sink(FormatterPtr formatter) : formatter(formatter) {

	}
	/**
	 * Default destructor.
     */
	virtual ~Sink() {}

	FormatterPtr getFormatter() const {
		return formatter;
	}

	void setFormatter(FormatterPtr formatter) {
		this->formatter = formatter;
	}

	std::string formatMessage(EntryContext const& context, std::string const& message) const {
		return (*formatter)(context, message);
	}

	/**
	 * Logs the given message with context info
	 */
	virtual void log(EntryContext const& context, std::string const& message) const = 0;
};
typedef std::shared_ptr<Sink> SinkPtr;

/**
 * Logging sink that wraps an arbitrary `std::ostream`.
 * It is meant to be used for streams like `std::cout` or `std::cerr`.
 * A StreamSink may be given a log level, which filters out all entries
 * below that level. By default is logs all entries.
 */
class StreamSink: public Sink {
	/// Filtered loglevel
	LogLevel level;
	/// Output stream.
	mutable std::unique_ptr<std::ostream> os;

	LogLevel getLevel() const {
		return level;
	}

	void setLevel(LogLevel level) {
		this->level = level;
	}

	explicit StreamSink(std::ostream& _os) :
			level(LogLevel::ALL),
			os(new std::ostream(_os.rdbuf())) {}

	explicit StreamSink(std::string const& filename) :
			level(LogLevel::ALL),
			os(new std::ofstream(filename, std::ios::out)) {}

public:
	void log(EntryContext const& context, std::string const& message) const override {
		if (context.level >= this->level) {
			*os << formatMessage(context, message) << std::flush;
		}
	}

	/**
	 * Create a StreamSink from some output stream.
     * @param os Output stream.
     */
	static SinkPtr create(std::ostream& os) {
		return SinkPtr(new StreamSink(os));
	}

	/**
	 * Create a StreamSink from some output file.
     * @param filename Filename for output file.
     */
	static SinkPtr create(std::string const& filename) {
		return SinkPtr(new StreamSink(filename));
	}
};

}

