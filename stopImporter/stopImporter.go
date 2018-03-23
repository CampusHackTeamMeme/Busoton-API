package main

import (
	"archive/zip"
	"bufio"
	"database/sql"
	"encoding/csv"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"

	pq "github.com/lib/pq"
)

func main() {
	getData()
	Unzip("NaPTAN.zip", ".")
	postgresImport(csvParser())

	deleteExtraFiles()
}

func getData() {
	out, err := os.Create("NaPTAN.zip")
	if err != nil {
		panic(err)
	}

	defer out.Close()
	resp, err := http.Get("http://naptan.app.dft.gov.uk/DataRequest/Naptan.ashx?format=csv")
	if err != nil {
		panic(err)
	}

	_, err = io.Copy(out, resp.Body)
	if err != nil {
		panic(err)
	}

	err = out.Close()
	if err != nil {
		panic(err)
	}
}

func csvParser() [][]string {
	inputFile, _ := os.Open("Stops.csv")
	defer inputFile.Close()

	reader := csv.NewReader(bufio.NewReader(inputFile))

	var skimmed [][]string

	reader.Read()

	for {
		record, err := reader.Read()
		if err != nil {
			break
		}
		skimmed = append(skimmed, []string{record[0], record[4], record[29], record[30]})
	}

	return skimmed
}

func connectionInfo() string {
	configFile, err := os.Open("postgres.config")
	if err != nil {
		panic(err)
	}

	reader := bufio.NewReader(configFile)

	var config []byte

	//cut out source line
	reader.ReadLine()

	for {
		line, _, err := reader.ReadLine()
		if err != nil {
			break
		}

		config = append(config, line...)
		config = append(config, ' ')
	}

	return string(config)
}

func postgresImport(skimmed [][]string) {
	db, err := sql.Open("postgres", connectionInfo())
	if err != nil {
		panic(err)
	}

	db.Exec("DELETE FROM stops;")

	txn, err := db.Begin()
	if err != nil {
		panic(err)
	}

	stmt, err := txn.Prepare(pq.CopyIn("stops", "stop_id", "name", "lon", "lat"))
	if err != nil {
		fmt.Print(err.Error)
		panic(err)
	}

	for _, stop := range skimmed {
		lon, _ := strconv.ParseFloat(stop[2], 64)
		lat, _ := strconv.ParseFloat(stop[3], 64)
		stmt.Exec(stop[0], stop[1], lon, lat)
	}

	err = stmt.Close()
	if err != nil {
		panic(err)
	}

	err = txn.Commit()
	if err != nil {
		panic(err)
	}
}

func Unzip(src, dest string) error {
	r, err := zip.OpenReader(src)
	if err != nil {
		return err
	}
	defer func() {
		if err := r.Close(); err != nil {
			panic(err)
		}
	}()

	os.MkdirAll(dest, 0755)

	// Closure to address file descriptors issue with all the deferred .Close() methods
	extractAndWriteFile := func(f *zip.File) error {
		rc, err := f.Open()
		if err != nil {
			return err
		}
		defer func() {
			if err := rc.Close(); err != nil {
				panic(err)
			}
		}()

		path := filepath.Join(dest, f.Name)

		if f.FileInfo().IsDir() {
			os.MkdirAll(path, f.Mode())
		} else {
			os.MkdirAll(filepath.Dir(path), f.Mode())
			f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, f.Mode())
			if err != nil {
				return err
			}
			defer func() {
				if err := f.Close(); err != nil {
					panic(err)
				}
			}()

			_, err = io.Copy(f, rc)
			if err != nil {
				return err
			}
		}
		return nil
	}

	for _, f := range r.File {
		if f.Name == "Stops.csv" {
			err := extractAndWriteFile(f)
			if err != nil {
				return err
			}
		}
	}

	return nil
}

func deleteExtraFiles() {
	os.Remove("NaPTAN.zip")
	os.Remove("Stops.csv")
}
